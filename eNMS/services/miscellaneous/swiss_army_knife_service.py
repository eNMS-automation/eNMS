from flask_mail import Message
from git import Repo
from git.exc import GitCommandError
from json import dumps
from logging import info
from os import remove
from pathlib import Path
from requests import post, get
from slackclient import SlackClient
from sqlalchemy import Boolean, Column, ForeignKey, Integer
from typing import Optional
from wtforms import BooleanField, HiddenField

from eNMS.forms.automation import ServiceForm
from eNMS.controller import controller
from eNMS.database.functions import factory, fetch_all
from eNMS.extensions import mail_client
from eNMS.models.automation import Service
from eNMS.models.inventory import Device


class SwissArmyKnifeService(Service):

    __tablename__ = "SwissArmyKnifeService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "SwissArmyKnifeService"}

    def job(self, *args):
        return getattr(self, self.name)(*args)

    def Start(self, _: dict, device: Optional[Device] = None) -> dict:  # noqa: N802
        return {"success": True}

    def End(self, _: dict, device: Optional[Device] = None) -> dict:  # noqa: N802
        return {"success": True}

    def mail_feedback_notification(self, payload: dict) -> dict:
        name = f"{payload['job']['name']}"
        recipients = payload["job"]["mail_recipient"].split(
            ","
        ) or controller.mail_recipients.split(",")
        self.logs.append(f"Sending mail notification for {name}")
        message = Message(
            f"{name} ({'PASS' if payload['result'] else 'FAILED'})",
            sender=controller.mail_sender,
            recipients=recipients,
            body=payload["content"],
        )
        runtime = payload["runtime"].replace(".", "").replace(":", "")
        filename = f"results-{runtime}.txt"
        with open(filename, "w") as file:
            file.write(controller.str_dict(payload["results"][payload["runtime"]]))
        with open(filename, "r") as file:
            message.attach(
                filename,
                "text/plain",
                file.read(),
                disposition=f"attachment; filename={filename}",
            )
        remove(filename)
        mail_client.send(message)
        return {"success": True}

    def slack_feedback_notification(self, payload: dict) -> dict:
        slack_client = SlackClient(controller.slack_token)
        self.logs.append(f"Sending Slack notification for {payload['job']['name']}")
        result = slack_client.api_call(
            "chat.postMessage",
            channel=controller.slack_channel,
            text=controller.str_dict(payload["content"]),
        )
        return {"success": True, "result": str(result)}

    def mattermost_feedback_notification(self, payload: dict) -> dict:
        self.logs.append(
            f"Sending Mattermost notification for {payload['job']['name']}"
        )
        post(
            controller.mattermost_url,
            verify=controller.mattermost_verify_certificate,
            data=dumps(
                {"channel": controller.mattermost_channel, "text": payload["content"]}
            ),
        )
        return {"success": True}

    def cluster_monitoring(self, payload: dict) -> dict:
        protocol = controller.cluster_scan_protocol
        for instance in fetch_all("Instance"):
            factory(
                "Instance",
                **get(
                    f"{protocol}://{instance.ip_address}/rest/is_alive",
                    timeout=controller.cluster_scan_timeout,
                ).json(),
            )
        return {"success": True}

    def poller_service(self, payload: dict) -> dict:
        for service in fetch_all("Service"):
            if getattr(service, "configuration_backup_service", False):
                service.try_run()
        for pool in fetch_all("Pool"):
            if pool.device_current_configuration:
                pool.compute_pool()
        return {"success": True}

    def git_push_configurations(self, payload: dict) -> dict:
        if controller.git_configurations:
            repo = Repo(Path.cwd() / "git" / "configurations")
            try:
                repo.remotes.origin.pull()
                repo.git.add(A=True)
                repo.git.commit(m="Automatic commit (configurations)")
            except GitCommandError as e:
                info(f"Git commit failed ({str(e)}")
            repo.remotes.origin.push()
        return {"success": True}

    def process_payload1(self, payload: dict, device: Device) -> dict:
        get_facts = payload["get_facts"]["results"]["devices"][device.name]
        # we use the name of the device to get the result for that particular
        # device.
        # all of the other inventory properties of the device are available
        # to use, including custom properties.
        uptime_less_than_50000 = get_facts["result"]["get_facts"]["uptime"] < 50000
        return {"success": True, "uptime_less_5000": uptime_less_than_50000}


class SwissArmyKnifeForm(ServiceForm):
    form_type = HiddenField(default="SwissArmyKnifeService")
    has_targets = BooleanField()

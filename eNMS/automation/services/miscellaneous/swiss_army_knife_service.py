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
from typing import overload

from eNMS.main import mail_client
from eNMS.automation.models import Service
from eNMS.base.classes import service_classes
from eNMS.base.helpers import factory, fetch_all, get_one, str_dict
from eNMS.inventory.models import Device


class SwissArmyKnifeService(Service):

    __tablename__ = "SwissArmyKnifeService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = Column(Boolean)

    __mapper_args__ = {"polymorphic_identity": "SwissArmyKnifeService"}

    @overload
    def job(self, payload: dict) -> dict:
        ...

    @overload
    def job(self, device: Device, payload: dict) -> dict:
        ...

    def job(self, *args):
        return getattr(self, self.name)(*args)

    def Start(self, _) -> dict:  # noqa: N802
        # Start of a workflow
        return {"success": True}

    def End(self, _) -> dict:  # noqa: N802
        # End of a workflow
        return {"success": True}

    def mail_feedback_notification(self, payload: dict) -> dict:
        parameters = get_one("Parameters")
        name, recipients = (
            payload["job"]["name"],
            (
                payload["job"]["mail_recipient"].split(",")
                or parameters.mail_recipients.split(",")
            ),
        )
        message = Message(
            name,
            sender=parameters.mail_sender,
            recipients=recipients,
            body=payload["result"],
        )
        runtime = payload["runtime"].replace(".", "").replace(":", "")
        filename = f"logs-{name}-{runtime}.txt"
        with open(filename, "w") as file:
            file.write(str_dict(payload["logs"][payload["runtime"]]))
        with open(filename, "r") as file:
            message.attach(filename, "text/plain", file.read())
        remove(filename)
        mail_client.send(message)
        return {"success": True}

    def slack_feedback_notification(self, payload: dict) -> dict:
        parameters = get_one("Parameters")
        slack_client = SlackClient(parameters.slack_token)
        result = slack_client.api_call(
            "chat.postMessage",
            channel=parameters.slack_channel,
            text=str_dict(payload["result"]),
        )
        return {"success": True, "result": str(result)}

    def mattermost_feedback_notification(self, payload: dict) -> dict:
        parameters = get_one("Parameters")
        post(
            parameters.mattermost_url,
            verify=parameters.mattermost_verify_certificate,
            data=dumps(
                {"channel": parameters.mattermost_channel, "text": payload["result"]}
            ),
        )
        return {"success": True}

    def cluster_monitoring(self, _) -> dict:
        parameters = get_one("Parameters")
        protocol = parameters.cluster_scan_protocol
        for instance in fetch_all("Instance"):
            factory(
                "Instance",
                **get(
                    f"{protocol}://{instance.ip_address}/rest/is_alive",
                    timeout=parameters.cluster_scan_timeout,
                ).json(),
            )
        return {"success": True}

    def poller_service(self, _) -> dict:
        for service in fetch_all("Service"):
            if getattr(service, "configuration_backup_service", False):
                service.try_run()
        return {"success": True}

    def git_push_configurations(self, _) -> dict:
        parameters = get_one("Parameters")
        if parameters.git_configurations:
            repo = Repo(Path.cwd() / "git" / "configurations")
            try:
                repo.git.add(A=True)
                repo.git.commit(m="Automatic commit (configurations)")
            except GitCommandError as e:
                info(f"Git commit failed ({str(e)}")
            repo.remotes.origin.push()
        return {"success": True}

    def process_payload1(self, device: Device, payload: dict) -> dict:
        get_facts = payload["get_facts"]
        # we use the name of the device to get the result for that particular
        # device.
        # all of the other inventory properties of the device are available
        # to use, including custom properties.
        results = get_facts["result"]["devices"][device.name]["result"]
        uptime_less_than_50000 = results["get_facts"]["uptime"] < 50000
        return {"success": True, "result": {"uptime_less_5000": uptime_less_than_50000}}


service_classes["SwissArmyKnifeService"] = SwissArmyKnifeService

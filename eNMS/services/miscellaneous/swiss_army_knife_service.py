from git import Repo
from git.exc import GitCommandError
from json import dumps
from logging import info
from pathlib import Path
from requests import post, get
from slackclient import SlackClient
from sqlalchemy import Boolean, Column, ForeignKey, Integer
from wtforms import BooleanField, HiddenField

from eNMS.forms.automation import ServiceForm
from eNMS.controller import controller
from eNMS.database import Session
from eNMS.database.functions import factory, fetch_all
from eNMS.models.automation import Service
from eNMS.models.inventory import Device


class SwissArmyKnifeService(Service):

    __tablename__ = "SwissArmyKnifeService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "SwissArmyKnifeService"}

    def job(self, *args, **kwargs):
        return getattr(self, self.name)(*args, **kwargs)

    def Start(self, *args, **kwargs) -> dict:  # noqa: N802
        return {"success": True}

    def End(self, *args, **kwargs) -> dict:  # noqa: N802
        return {"success": True}

    def mail_feedback_notification(self, run: "Run") -> dict:
        name = f"{run.payload['job']['name']}"
        recipients = run.payload["job"]["mail_recipient"]
        runtime = run.payload["results"]["timestamp"].replace(".", "").replace(":", "")
        filename = f"results-{runtime}.txt"
        controller.send_email(
            f"{name} ({'PASS' if run.payload['results']['success'] else 'FAILED'})",
            run.payload["content"],
            recipients=recipients,
            filename=filename,
            file_content=controller.str_dict(run.payload["results"]),
        )
        return {"success": True}

    def slack_feedback_notification(self, run: "Run") -> dict:
        slack_client = SlackClient(controller.slack_token)
        result = slack_client.api_call(
            "chat.postMessage",
            channel=controller.slack_channel,
            text=controller.str_dict(run.payload["content"]),
        )
        return {"success": True, "result": str(result)}

    def mattermost_feedback_notification(self, run: "Run") -> dict:
        post(
            controller.mattermost_url,
            verify=controller.mattermost_verify_certificate,
            data=dumps(
                {"channel": controller.mattermost_channel, "text": run.payload["content"]}
            ),
        )
        return {"success": True}

    def cluster_monitoring(self, run: "Run") -> dict:
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

    def poller_service(self, run: "Run") -> dict:
        for service in fetch_all("Service"):
            if getattr(service, "configuration_backup_service", False):
                service.run()
        Session.commit()
        for pool in fetch_all("Pool"):
            if pool.device_current_configuration:
                pool.compute_pool()
        return {"success": True}

    def git_push_configurations(self, run: "Run") -> dict:
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

    def process_run.payload1(self, run: "Run", device: Device) -> dict:
        # we use the name of the device to get the result for that particular
        # device.
        get_facts = run.payload["get_facts"]["results"]["devices"][device.name]
        get_interfaces = run.payload["get_interfaces"]["results"]["devices"][device.name]
        uptime_less_than_50000 = get_facts["result"]["get_facts"]["uptime"] < 50000
        mgmg1_is_up = get_interfaces["result"]["get_interfaces"]["Management1"]["is_up"]
        return {
            "success": True,
            "uptime_less_5000": uptime_less_than_50000,
            "Management1 is UP": mgmg1_is_up,
        }


class SwissArmyKnifeForm(ServiceForm):
    form_type = HiddenField(default="SwissArmyKnifeService")
    has_targets = BooleanField("Has Target Devices")

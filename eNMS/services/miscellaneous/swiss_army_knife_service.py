from git import Repo
from git.exc import GitCommandError
from json import dumps
from logging import info
from pathlib import Path
from requests import post, get
from slackclient import SlackClient
from sqlalchemy import Boolean, ForeignKey, Integer
from wtforms import BooleanField, HiddenField

from eNMS.controller.concurrency import run_job
from eNMS import app
from eNMS.database import Session
from eNMS.database.dialect import Column
from eNMS.database.functions import factory, fetch_all
from eNMS.forms.automation import ServiceForm
from eNMS.models.automation import Run, Service
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

    def mail_feedback_notification(self, run: "Run", payload: dict) -> dict:
        name = payload["job"]["name"]
        recipients = payload["run"]["mail_recipient"]
        runtime = run.runtime.replace(".", "").replace(":", "")
        filename = f"results-{runtime}.txt"
        app.send_email(
            f"{name} ({'PASS' if payload['results']['success'] else 'FAILED'})",
            payload["content"],
            recipients=recipients,
            filename=filename,
            file_content=app.str_dict(payload["results"]),
        )
        return {"success": True}

    def slack_feedback_notification(self, run: "Run", payload: dict) -> dict:
        slack_client = SlackClient(app.slack_token)
        result = slack_client.api_call(
            "chat.postMessage",
            channel=app.slack_channel,
            text=app.str_dict(payload["content"]),
        )
        return {"success": True, "result": str(result)}

    def mattermost_feedback_notification(self, run: "Run", payload: dict) -> dict:
        post(
            app.mattermost_url,
            verify=app.mattermost_verify_certificate,
            data=dumps(
                {"channel": app.mattermost_channel, "text": payload["content"]}
            ),
        )
        return {"success": True}

    def cluster_monitoring(self, run: "Run", payload: dict) -> dict:
        protocol = app.cluster_scan_protocol
        for instance in fetch_all("Instance"):
            factory(
                "Instance",
                **get(
                    f"{protocol}://{instance.ip_address}/rest/is_alive",
                    timeout=app.cluster_scan_timeout,
                ).json(),
            )
        return {"success": True}

    def poller_service(self, run: "Run", payload: dict) -> dict:
        for service in fetch_all("Service"):
            if getattr(service, "configuration_backup_service", False):
                run_job(service.id)
        Session.commit()
        for pool in fetch_all("Pool"):
            if pool.device_current_configuration:
                pool.compute_pool()
        return {"success": True}

    def git_push_configurations(self, run: "Run", payload: dict) -> dict:
        if app.git_configurations:
            repo = Repo(Path.cwd() / "git" / "configurations")
            try:
                repo.remotes.origin.pull()
                repo.git.add(A=True)
                repo.git.commit(m="Automatic commit (configurations)")
            except GitCommandError as e:
                info(f"Git commit failed ({str(e)}")
            repo.remotes.origin.push()
        return {"success": True}

    def process_payload1(self, run: "Run", payload: dict, device: Device) -> dict:
        # we use the name of the device to get the result for that particular device.
        get_facts = run.get_result("get_facts", device.name)
        get_interfaces = run.get_result("get_interfaces", device.name)
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

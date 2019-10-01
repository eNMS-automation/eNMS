from git import Repo
from git.exc import GitCommandError
from json import dumps
from logging import info
from pathlib import Path
from requests import post, get
from slackclient import SlackClient
from sqlalchemy import ForeignKey, Integer
from wtforms import HiddenField

from eNMS import app
from eNMS.database import Session
from eNMS.database.dialect import Column
from eNMS.database.functions import factory, fetch_all
from eNMS.forms.automation import ServiceForm
from eNMS.models.automation import Service


class SwissArmyKnifeService(Service):

    __tablename__ = "swiss_army_knife_service"
    pretty_name = "Swiss Army Knife"

    id = Column(Integer, ForeignKey("service.id"), primary_key=True)

    __mapper_args__ = {"polymorphic_identity": "swiss_army_knife_service"}

    def job(self, *args, **kwargs):
        return getattr(self, self.name)(*args, **kwargs)

    def Start(self, *args, **kwargs):  # noqa: N802
        return {"success": True}

    def End(self, *args, **kwargs):  # noqa: N802
        return {"success": True}

    def mail_feedback_notification(self, run, payload):
        name = payload["service"]["name"]
        app.send_email(
            f"{name} ({'PASS' if payload['results']['success'] else 'FAILED'})",
            payload["content"],
            recipients=payload["service"]["mail_recipient"],
            filename=f"results-{run.runtime.replace('.', '').replace(':', '')}.txt",
            file_content=app.str_dict(payload["results"]),
        )
        return {"success": True}

    def slack_feedback_notification(self, run, payload):
        slack_client = SlackClient(app.slack_token)
        result = slack_client.api_call(
            "chat.postMessage",
            channel=app.slack_channel,
            text=app.str_dict(payload["content"]),
        )
        return {"success": True, "result": str(result)}

    def mattermost_feedback_notification(self, run, payload):
        post(
            app.mattermost_url,
            verify=app.mattermost_verify_certificate,
            data=dumps({"channel": app.mattermost_channel, "text": payload["content"]}),
        )
        return {"success": True}

    def cluster_monitoring(self, run, payload):
        protocol = app.cluster_scan_protocol
        for instance in fetch_all("instance"):
            factory(
                "instance",
                **get(
                    f"{protocol}://{instance.ip_address}/rest/is_alive",
                    timeout=app.cluster_scan_timeout,
                ).json(),
            )
        return {"success": True}

    def git_push_configurations(self, run, payload):
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

    def process_payload1(self, run, payload, device):
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
    form_type = HiddenField(default="swiss_army_knife_service")

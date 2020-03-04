from os import environ
from slackclient import SlackClient
from sqlalchemy import ForeignKey, Integer
from wtforms.widgets import TextArea

from eNMS import app
from eNMS.database.dialect import Column, LargeString, SmallString
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import HiddenField, StringField
from eNMS.models.automation import Service


class SlackNotificationService(Service):

    __tablename__ = "slack_notification_service"
    pretty_name = "Slack Notification"
    id = Column(Integer, ForeignKey("service.id"), primary_key=True)
    channel = Column(SmallString)
    token = Column(SmallString)
    body = Column(LargeString, default="")

    __mapper_args__ = {"polymorphic_identity": "slack_notification_service"}

    def job(self, run, payload, device=None):
        slack_client = SlackClient(run.token or environ.get("SLACK_TOKEN"))
        channel = run.sub(run.channel, locals()) or app.settings["slack"]["channel"]
        run.log("info", f"Sending SLACK notification on {channel}", device)
        result = slack_client.api_call(
            "chat.postMessage", channel=channel, text=run.sub(run.body, locals())
        )
        return {"success": True, "result": str(result)}


class SlackNotificationForm(ServiceForm):
    form_type = HiddenField(default="slack_notification_service")
    channel = StringField(substitution=True)
    token = StringField()
    body = StringField(widget=TextArea(), render_kw={"rows": 5}, substitution=True)

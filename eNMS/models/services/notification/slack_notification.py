from os import getenv
from sqlalchemy import ForeignKey, Integer
from warnings import warn
from wtforms.widgets import TextArea

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
except ImportError as exc:
    warn(f"Couldn't import slack_sdk module ({exc})")

from eNMS.database import db
from eNMS.forms import ServiceForm
from eNMS.fields import HiddenField, StringField
from eNMS.models.automation import Service
from eNMS.variables import vs


class SlackNotificationService(Service):
    __tablename__ = "slack_notification_service"
    pretty_name = "Slack Notification"
    id = db.Column(Integer, ForeignKey("service.id"), primary_key=True)
    channel = db.Column(db.SmallString)
    token = db.Column(db.SmallString)
    body = db.Column(db.LargeString)

    __mapper_args__ = {"polymorphic_identity": "slack_notification_service"}

    def job(self, run, device=None):
        client = WebClient(token=run.token or getenv("SLACK_TOKEN"))
        channel = run.sub(run.channel, locals()) or vs.settings["slack"]["channel"]
        message = run.sub(run.body, locals())
        run.log("info", f"Sending SLACK notification on {channel}", device)
        try:
            result = client.chat_postMessage(channel=f"#{channel}", text=message)
            return {"success": True, "result": str(result)}
        except SlackApiError as exc:
            return {"success": False, "result": exc.response}


class SlackNotificationForm(ServiceForm):
    form_type = HiddenField(default="slack_notification_service")
    channel = StringField(substitution=True)
    token = StringField()
    body = StringField(widget=TextArea(), render_kw={"rows": 5}, substitution=True)

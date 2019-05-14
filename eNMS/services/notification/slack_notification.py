from slackclient import SlackClient
from sqlalchemy import Column, ForeignKey, Integer, String, Text
from wtforms import HiddenField, StringField
from wtforms.widgets import TextArea

from eNMS.database import LARGE_STRING_LENGTH, SMALL_STRING_LENGTH
from eNMS.database.functions import get_one
from eNMS.forms.automation import ServiceForm
from eNMS.models.automation import Service


class SlackNotificationService(Service):

    __tablename__ = "SlackNotificationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    channel = Column(String(SMALL_STRING_LENGTH), default="")
    token = Column(String(SMALL_STRING_LENGTH), default="")
    body = Column(Text(LARGE_STRING_LENGTH), default="")

    __mapper_args__ = {"polymorphic_identity": "SlackNotificationService"}

    def job(self, _) -> dict:
        parameters = get_one("Parameters")
        slack_client = SlackClient(self.token or parameters.slack_token)
        channel = self.channel or parameters.slack_channel
        self.logs.append(f"Sending Slack notification on {channel}")
        result = slack_client.api_call(
            "chat.postMessage", channel=channel, text=self.sub(self.body, locals())
        )
        return {"success": True, "result": str(result)}


class SlackNotificationForm(ServiceForm):
    form_type = HiddenField(default="SlackNotificationService")
    channel = StringField("Channel")
    token = StringField()
    body = StringField(widget=TextArea(), render_kw={"rows": 5})

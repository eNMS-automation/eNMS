from slackclient import SlackClient
from sqlalchemy import Column, ForeignKey, Integer, String

from eNMS.functions import get_one
from eNMS.automation.models import Service
from eNMS.classes import service_classes


class SlackNotificationService(Service):

    __tablename__ = "SlackNotificationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    channel = Column(String(255))
    token = Column(String(255))
    body = Column(String(255))
    body_textarea = True

    __mapper_args__ = {"polymorphic_identity": "SlackNotificationService"}

    def job(self, _) -> dict:
        parameters = get_one("Parameters")
        slack_client = SlackClient(self.token or parameters.slack_token)
        channel = self.channel or parameters.slack_channel
        self.logs.append(f"Sending Slack notification on {channel}")
        result = slack_client.api_call(
            "chat.postMessage", channel=channel, text=self.body
        )
        return {"success": True, "result": str(result)}


service_classes["SlackNotificationService"] = SlackNotificationService

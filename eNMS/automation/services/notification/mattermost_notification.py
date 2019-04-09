from json import dumps
from requests import post
from sqlalchemy import Column, ForeignKey, Integer, String

from eNMS.functions import get_one
from eNMS.automation.models import Service
from eNMS.classes import service_classes


class MattermostNotificationService(Service):

    __tablename__ = "MattermostNotificationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    channel = Column(String(255))
    body = Column(String(255))
    body_textarea = True

    __mapper_args__ = {"polymorphic_identity": "MattermostNotificationService"}

    def job(self, _) -> dict:
        parameters = get_one("Parameters")
        channel = self.channel or parameters.mattermost_channel
        self.logs.append(f"Sending Mattermost notification on {channel}")
        result = post(
            parameters.mattermost_url,
            verify=parameters.mattermost_verify_certificate,
            data=dumps({"channel": channel, "text": self.body}),
        )
        return {"success": True, "result": str(result)}


service_classes["MattermostNotificationService"] = MattermostNotificationService

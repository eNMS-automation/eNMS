from json import dumps
from requests import post
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from typing import Optional
from wtforms import HiddenField, StringField
from wtforms.widgets import TextArea

from eNMS.controller import controller
from eNMS.database import LARGE_STRING_LENGTH, SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.models.automation import Service
from eNMS.models.inventory import Device


class MattermostNotificationService(Service):

    __tablename__ = "MattermostNotificationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = Column(Boolean, default=False)
    channel = Column(String(SMALL_STRING_LENGTH), default="")
    body = Column(Text(LARGE_STRING_LENGTH), default="")

    __mapper_args__ = {"polymorphic_identity": "MattermostNotificationService"}

    def job(self, payload: dict, device: Optional[Device] = None) -> dict:
        channel = self.sub(self.channel, locals()) or controller.mattermost_channel
        self.logs.append(f"Sending Mattermost notification on {channel}")
        result = post(
            controller.mattermost_url,
            verify=controller.mattermost_verify_certificate,
            data=dumps({"channel": channel, "text": self.sub(self.body, locals())}),
        )
        return {"success": True, "result": str(result)}


class MattermostNotificationForm(ServiceForm):
    form_type = HiddenField(default="MattermostNotificationService")
    channel = StringField()
    body = StringField(widget=TextArea(), render_kw={"rows": 5})

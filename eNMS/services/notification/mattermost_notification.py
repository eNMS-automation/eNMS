from json import dumps
from requests import post
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from typing import Optional
from wtforms import HiddenField
from wtforms.widgets import TextArea

from eNMS.controller import controller
from eNMS.database import LARGE_STRING_LENGTH, SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.models.automation import Job, Service
from eNMS.models.inventory import Device


class MattermostNotificationService(Service):

    __tablename__ = "MattermostNotificationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = Column(Boolean, default=False)
    channel = Column(String(SMALL_STRING_LENGTH), default="")
    body = Column(Text(LARGE_STRING_LENGTH), default="")

    __mapper_args__ = {"polymorphic_identity": "MattermostNotificationService"}

    def job(
        self,
        payload: dict,
        timestamp: str,
        device: Optional[Device] = None,
        parent: Optional[Job] = None,
    ) -> dict:
        channel = self.sub(self.channel, locals()) or controller.mattermost_channel
        self.log(timestamp, "info", f"Sending Mattermost notification on {channel}")
        result = post(
            controller.mattermost_url,
            verify=controller.mattermost_verify_certificate,
            data=dumps({"channel": channel, "text": self.sub(self.body, locals())}),
        )
        return {"success": True, "result": str(result)}


class MattermostNotificationForm(ServiceForm):
    form_type = HiddenField(default="MattermostNotificationService")
    channel = SubstitutionField()
    body = SubstitutionField(widget=TextArea(), render_kw={"rows": 5})

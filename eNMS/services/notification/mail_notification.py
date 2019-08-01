from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from typing import Optional
from wtforms import HiddenField, StringField
from wtforms.widgets import TextArea

from eNMS.controller import controller
from eNMS.database import LARGE_STRING_LENGTH, SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.models.automation import Run, Service
from eNMS.models.inventory import Device


class MailNotificationService(Service):

    __tablename__ = "MailNotificationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = Column(Boolean, default=False)
    title = Column(String(SMALL_STRING_LENGTH), default="")
    sender = Column(String(SMALL_STRING_LENGTH), default="")
    recipients = Column(String(SMALL_STRING_LENGTH), default="")
    body = Column(Text(LARGE_STRING_LENGTH), default="")

    __mapper_args__ = {"polymorphic_identity": "MailNotificationService"}

    def job(self, run: "Run", payload: dict, device: Optional[Device] = None) -> dict:
        controller.send_email(
            run.sub(run["title"], locals()),
            run.sub(run["body"], locals()),
            sender=run["sender"],
            recipients=run["recipients"],
        )
        return {"success": True, "result": {}}


class MailNotificationForm(ServiceForm):
    form_type = HiddenField(default="MailNotificationService")
    title = SubstitutionField()
    sender = StringField()
    recipients = StringField()
    body = SubstitutionField(widget=TextArea(), render_kw={"rows": 5})

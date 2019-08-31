from sqlalchemy import Boolean, ForeignKey, Integer
from typing import Optional
from wtforms import HiddenField, StringField
from wtforms.widgets import TextArea

from eNMS import app
from eNMS.database.dialect import Column, LargeString, SmallString
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.models.automation import Service
from eNMS.models.execution import Run
from eNMS.models.inventory import Device


class MailNotificationService(Service):

    __tablename__ = "MailNotificationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = Column(Boolean, default=False)
    title = Column(SmallString)
    sender = Column(SmallString)
    recipients = Column(SmallString)
    body = Column(LargeString, default="")

    __mapper_args__ = {"polymorphic_identity": "MailNotificationService"}

    def job(self, run: "Run", payload: dict, device: Optional[Device] = None) -> dict:
        app.send_email(
            run.sub(run.title, locals()),
            run.sub(run.body, locals()),
            sender=run.sender,
            recipients=run.recipients,
        )
        return {"success": True, "result": {}}


class MailNotificationForm(ServiceForm):
    form_type = HiddenField(default="MailNotificationService")
    title = SubstitutionField()
    sender = StringField()
    recipients = StringField()
    body = SubstitutionField(widget=TextArea(), render_kw={"rows": 5})

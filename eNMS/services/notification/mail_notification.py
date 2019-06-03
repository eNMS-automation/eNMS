from flask_mail import Message
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from typing import Optional
from wtforms import HiddenField, StringField
from wtforms.widgets import TextArea

from eNMS.controller import controller
from eNMS.database import LARGE_STRING_LENGTH, SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.extensions import mail_client
from eNMS.models.automation import Service
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

    def job(self, payload: dict, device: Optional[Device] = None) -> dict:
        if self.recipients:
            recipients = self.recipients.split(",")
        else:
            recipients = controller.mail_sender.split(",")
        sender = self.sender or controller.mail_sender
        title = self.sub(self.title, locals())
        body = self.sub(self.body, locals())
        self.logs.append(f"Sending mail {title} to {sender}")
        app_context = controller.app.app_context()
        app_context.push()
        message = Message(title, sender=sender, recipients=recipients, body=body)
        mail_client.send(message)
        return {"success": True, "result": {}}


class MailNotificationForm(ServiceForm):
    form_type = HiddenField(default="MailNotificationService")
    title = StringField()
    sender = StringField()
    recipients = StringField()
    body = StringField(widget=TextArea(), render_kw={"rows": 5})

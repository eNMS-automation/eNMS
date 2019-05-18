from flask_mail import Message
from sqlalchemy import Column, ForeignKey, Integer, String, Text
from wtforms import HiddenField, StringField
from wtforms.widgets import TextArea

from eNMS.controller import controller
from eNMS.database import LARGE_STRING_LENGTH, SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.extensions import mail_client
from eNMS.models.automation import Service


class MailNotificationService(Service):

    __tablename__ = "MailNotificationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    title = Column(String(SMALL_STRING_LENGTH), default="")
    sender = Column(String(SMALL_STRING_LENGTH), default="")
    recipients = Column(String(SMALL_STRING_LENGTH), default="")
    body = Column(Text(LARGE_STRING_LENGTH), default="")

    __mapper_args__ = {"polymorphic_identity": "MailNotificationService"}

    def job(self, _) -> dict:
        if self.recipients:
            recipients = self.recipients.split(",")
        else:
            recipients = controller.mail_sender.split(",")
        sender = self.sender or controller.mail_sender
        title = self.sub(self.title, locals())
        body = self.sub(self.body, locals())
        self.logs.append(f"Sending mail {title} to {sender}")
        message = Message(title, sender=sender, recipients=recipients, body=body)
        mail_client.send(message)
        return {"success": True, "result": str(message)}


class MailNotificationForm(ServiceForm):
    form_type = HiddenField(default="MailNotificationService")
    title = StringField()
    sender = StringField()
    recipients = StringField()
    body = StringField(widget=TextArea(), render_kw={"rows": 5})

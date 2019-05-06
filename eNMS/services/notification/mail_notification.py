from flask_mail import Message
from sqlalchemy import Column, ForeignKey, Integer, String, Text
from wtforms import HiddenField, StringField
from wtforms.widgets import TextArea

from eNMS.database import LARGE_STRING_LENGTH, get_one, SMALL_STRING_LENGTH
from eNMS.forms import metaform
from eNMS.forms.automation import ServiceForm
from eNMS.modules import mail_client
from eNMS.models import metamodel
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
        parameters = get_one("Parameters")
        if self.recipients:
            recipients = self.recipients.split(",")
        else:
            recipients = parameters.mail_sender.split(",")
        sender = self.sender or parameters.mail_sender
        self.logs.append(f"Sending mail {self.title} to {sender}")
        message = Message(
            self.title, sender=sender, recipients=recipients, body=self.body
        )
        mail_client.send(message)
        return {"success": True, "result": str(message)}


class MailNotificationForm(ServiceForm, metaclass=metaform):
    form_type = HiddenField(default="MailNotificationService")
    title = StringField()
    sender = StringField()
    recipients = StringField()
    body = StringField(widget=TextArea(), render_kw={"rows": 5})

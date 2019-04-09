from flask_mail import Message
from sqlalchemy import Column, ForeignKey, Integer, String

from eNMS.extensions import mail_client
from eNMS.automation.models import Service
from eNMS.classes import service_classes
from eNMS.functions import get_one


class MailNotificationService(Service):

    __tablename__ = "MailNotificationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    title = Column(String(255))
    sender = Column(String(255))
    recipients = Column(String(255))
    body = Column(String(255))
    body_textarea = True

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


service_classes["MailNotificationService"] = MailNotificationService

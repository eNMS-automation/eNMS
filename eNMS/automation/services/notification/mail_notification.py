from flask_mail import Message
from sqlalchemy import Column, ForeignKey, Integer, String

from eNMS.main import mail_client
from eNMS.automation.models import Service
from eNMS.base.classes import service_classes
from eNMS.base.helpers import get_one


class MailNotificationService(Service):

    __tablename__ = 'MailNotificationService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    title = Column(String)
    sender = Column(String)
    recipients = Column(String)
    body = Column(String)
    body_textarea = True

    __mapper_args__ = {
        'polymorphic_identity': 'MailNotificationService',
    }

    def job(self, _):
        parameters = get_one('Parameters')
        if self.recipients:
            recipients = self.recipients.split(',')
        else:
            recipients = parameters.mail_sender.split(',')
        message = Message(
            self.title,
            sender=self.sender or parameters.mail_sender,
            recipients=recipients,
            body=self.body
        )
        mail_client.send(message)
        return {'success': True, 'result': str(message)}


service_classes['MailNotificationService'] = MailNotificationService

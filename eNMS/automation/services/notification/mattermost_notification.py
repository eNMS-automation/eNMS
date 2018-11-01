from flask_mail import Message
from netmiko import file_transfer
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String

from eNMS import mail
from eNMS.automation.models import Service
from eNMS.base.models import service_classes


class MattermostNotificationService(Service):

    __tablename__ = 'MattermostNotificationService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    title = Column(String)
    sender = Column(String)
    recipients = Column(String)
    body = Column(String)
    body_textarea = True
    multiprocessing = False

    __mapper_args__ = {
        'polymorphic_identity': 'mattermost_notification_service',
    }

    def job(self, _):
        message = Message(
            self.title,
            sender=self.sender,
            recipients=self.recipients.split(','),
            body=self.body
        )
        mail.send(message)
        return {'success': True, 'result': message}


service_classes['mattermost_notification_service'] = MattermostNotificationService

from netmiko import file_transfer
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String


from eNMS.automation.models import Service
from eNMS.base.models import service_classes


class MailNotificationService(Service):

    __tablename__ = 'MailNotificationService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    multiprocessing = False

    __mapper_args__ = {
        'polymorphic_identity': 'mail_notification_service',
    }

    def job(self, device, payload):
        return {'success': True, 'result': 'result'}


service_classes['mail_notification_service'] = MailNotificationService

from json import dumps
from requests import post
from sqlalchemy import Column, ForeignKey, Integer, String

from eNMS.base.helpers import get_one
from eNMS.automation.models import Service
from eNMS.base.models import service_classes as sc


class MattermostNotificationService(Service):

    __tablename__ = 'MattermostNotificationService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    channel = Column(String)
    body = Column(String)
    body_textarea = True
    multiprocessing = False

    __mapper_args__ = {
        'polymorphic_identity': 'mattermost_notification_service',
    }

    def job(self, _):
        parameters = get_one('Parameters')
        result = post(
            parameters.mattermost_url,
            data=dumps({
                "channel": self.channel or parameters.mattermost_channel,
                "text": self.body
            })
        )
        return {'success': True, 'result': str(result)}


sc['mattermost_notification_service'] = MattermostNotificationService

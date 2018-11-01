from json import dumps
from requests import post
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String

from eNMS.base.helpers import get_one
from eNMS.automation.models import Service
from eNMS.base.models import service_classes


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
        result = requests.post(
            get_one('Parameters').mattermost_url,
            data=json.dumps({
                "channel": self.channel,
                "text": self.body
            })
        )
        return {'success': True, 'result': result}


service_classes['mattermost_notification_service'] = MattermostNotificationService

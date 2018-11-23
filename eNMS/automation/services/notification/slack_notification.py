from slackclient import SlackClient
from sqlalchemy import Column, ForeignKey, Integer, String

from eNMS.base.helpers import get_one
from eNMS.automation.models import Service
from eNMS.base.classes import service_classes


class SlackNotificationService(Service):

    __tablename__ = 'SlackNotificationService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    channel = Column(String)
    token = Column(String)
    body = Column(String)
    body_textarea = True

    __mapper_args__ = {
        'polymorphic_identity': 'SlackNotificationService',
    }

    def job(self, _):
        parameters = get_one('Parameters')
        slack_client = SlackClient(self.token or parameters.slack_token)
        result = slack_client.api_call(
            'chat.postMessage',
            channel=self.channel or parameters.slack_channel,
            text=self.body
        )
        return {'success': True, 'result': str(result)}


service_classes['SlackNotificationService'] = SlackNotificationService

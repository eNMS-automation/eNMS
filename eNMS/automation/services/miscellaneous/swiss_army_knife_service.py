from flask_mail import Message
from git import Repo
from git.exc import GitCommandError
from json import dumps
from os import remove
from pathlib import Path
from requests import post, get
from slackclient import SlackClient
from sqlalchemy import Boolean, Column, ForeignKey, Integer

from eNMS.main import mail_client
from eNMS.automation.models import Service
from eNMS.base.classes import service_classes
from eNMS.base.helpers import factory, fetch_all, get_one, str_dict


class SwissArmyKnifeService(Service):

    __tablename__ = 'SwissArmyKnifeService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = Column(Boolean)

    __mapper_args__ = {
        'polymorphic_identity': 'SwissArmyKnifeService',
    }

    def job(self, *args):
        return getattr(self, self.name)(*args)

    def job1(self, device, payload):
        return {'success': True, 'result': ''}

    def job2(self, payload):
        return {'success': True, 'result': ''}

    def Start(self, *a, **kw):  # noqa: N802
        # Start of a workflow
        return {'success': True}

    def End(self, *a, **kw):  # noqa: N802
        # End of a workflow
        return {'success': True}

    def mail_feedback_notification(self, payload):
        parameters = get_one('Parameters')
        message = Message(
            payload['job']['name'],
            sender=parameters.mail_sender,
            recipients=parameters.mail_recipients.split(','),
            body=payload['result']
        )
        runtime = payload["runtime"].replace('.', '').replace(':', '')
        filename = f'logs-{runtime}.txt'
        with open(filename, 'w') as file:
            file.write(str_dict(payload["logs"][payload["runtime"]]))
        with open(filename, 'r') as file:
            message.attach(filename, 'text/plain', file.read())
        remove(filename)
        mail_client.send(message)
        return {'success': True}

    def slack_feedback_notification(self, payload):
        parameters = get_one('Parameters')
        slack_client = SlackClient(parameters.slack_token)
        result = slack_client.api_call(
            'chat.postMessage',
            channel=parameters.slack_channel,
            text=str_dict(payload['result'])
        )
        return {'success': True, 'result': str(result)}

    def mattermost_feedback_notification(self, payload):
        parameters = get_one('Parameters')
        post(parameters.mattermost_url, data=dumps({
            'channel': parameters.mattermost_channel,
            'text': payload['result']
        }))
        return {'success': True}

    def cluster_monitoring(self, _):
        parameters = get_one('Parameters')
        protocol = parameters.cluster_scan_protocol
        for instance in fetch_all('Instance'):
            factory('Instance', **get(
                f'{protocol}://{instance.ip_address}/rest/is_alive',
                timeout=parameters.cluster_scan_timeout
            ).json())
        return {'success': True}

    def git_push_configurations(self, _):
        parameters = get_one('Parameters')
        if parameters.git_repository_configurations:
            repo = Repo(Path.cwd() / 'git' / 'configurations')
            try:
                repo.git.add(A=True)
                repo.git.commit(m='Automatic commit (configurations)')
            except GitCommandError:
                pass
            repo.remotes.origin.push()
        return {'success': True}

    def process_payload1(self, device, payload):
        get_facts = payload['get_facts']
        # we use the name of the device to get the result for that particular
        # device.
        # all of the other inventory properties of the device are available
        # to use, including custom properties.
        results = get_facts['result']['devices'][device.name]['result']
        uptime_less_than_50000 = results['get_facts']['uptime'] < 50000
        return {
            'success': True,
            'result': {
                'uptime_less_5000': uptime_less_than_50000
            }
        }


service_classes['SwissArmyKnifeService'] = SwissArmyKnifeService

from json import dumps, loads
from netmiko import file_transfer
from re import search
from requests import (
    get as rest_get,
    post as rest_post,
    put as rest_put,
    delete as rest_delete
)
from requests.auth import HTTPBasicAuth
from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    PickleType,
    String
)
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import relationship
from subprocess import check_output

from eNMS.base.custom_base import CustomBase
from eNMS.base.helpers import str_dict
from eNMS.services.connections import napalm_connection, netmiko_connection
from eNMS.services.properties import type_to_properties


def multiprocessing(function):
    def wrapper(self, args):
        task, device, results, incoming_payload = args
        success, result, payload = function(self, *args)
        if 'logs' in results:
            results['logs'][device.name] = result
            results['payload']['outgoing_payload'][device.name] = payload
        else:
            results['logs'] = {device.name: result}
            results['payload'] = {
                'incoming_payload': incoming_payload,
                'outgoing_payload': {device.name: payload}
            }
        if 'success' not in results or results['success']:
            results['success'] = success
    return wrapper


class Job(CustomBase):

    __tablename__ = 'Job'

    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True)
    description = Column(String)
    type = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'Job',
        'polymorphic_on': type
    }


class Service(Job):

    __tablename__ = 'Service'

    id = Column(Integer, ForeignKey('Job.id'), primary_key=True)
    tasks = relationship('ServiceTask', back_populates='service')

    __mapper_args__ = {
        'polymorphic_identity': 'service',
    }

    @property
    def properties(self):
        custom_properties = type_to_properties['custom_service']
        return {
            p: getattr(self, p)
            for p in type_to_properties.get(self.type, custom_properties)
        }

    @property
    def serialized(self):
        properties = self.properties
        properties['tasks'] = [obj.properties for obj in getattr(self, 'tasks')]
        return properties


class AnsibleService(Service):

    __tablename__ = 'AnsibleService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    vendor = Column(String)
    operating_system = Column(String)
    playbook_path = Column(String)
    arguments = Column(String)
    content_match = Column(String)
    content_match_regex = Column(Boolean)
    options = Column(MutableDict.as_mutable(PickleType), default={})
    pass_device_properties = Column(Boolean)
    inventory_from_selection = Column(Boolean)
    device_multiprocessing = True

    __mapper_args__ = {
        'polymorphic_identity': 'ansible_playbook',
    }

    @multiprocessing
    def job(self, task, device, results, incoming_payload):
        try:
            arguments = self.arguments.split()
            command = ['ansible-playbook']
            if self.pass_device_properties:
                command.extend(['-e', dumps(device.properties)])
            if self.inventory_from_selection:
                command.extend(['-i', device.ip_address + ','])
            command.append(self.playbook_path)
            result = check_output(command + arguments)
            try:
                result = result.decode('utf-8')
            except AttributeError:
                pass
            if self.content_match_regex:
                success = bool(search(self.content_match, str(result)))
            else:
                success = self.content_match in str(result)
        except Exception as e:
            success, result = False, str(e)
        return success, result, incoming_payload


class RestCallService(Service):

    __tablename__ = 'RestCallService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    call_type = Column(String)
    url = Column(String)
    payload = Column(MutableDict.as_mutable(PickleType), default={})
    content_match = Column(String)
    content_match_regex = Column(Boolean)
    username = Column(String)
    password = Column(String)
    device_multiprocessing = False
    request_dict = {
        'GET': rest_get,
        'POST': rest_post,
        'PUT': rest_put,
        'DELETE': rest_delete
    }

    __mapper_args__ = {
        'polymorphic_identity': 'rest_call',
    }

    def job(self, task, results, incoming_payload):
        try:
            if self.call_type in ('GET', 'DELETE'):
                result = self.request_dict[self.call_type](
                    self.url,
                    headers={'Accept': 'application/json'},
                    auth=HTTPBasicAuth(self.username, self.password)
                ).json()
            else:
                result = loads(self.request_dict[self.call_type](
                    self.url,
                    data=dumps(self.payload),
                    auth=HTTPBasicAuth(self.username, self.password)
                ).content)
            if self.content_match_regex:
                success = bool(search(self.content_match, str(result)))
            else:
                success = self.content_match in str(result)
            if isinstance(incoming_payload, dict):
                incoming_payload[self.name] = result
            else:
                incoming_payload = {self.name: result}
        except Exception as e:
            result, success = str(e), False
        return {
            'success': success,
            'payload': {
                'incoming_payload': incoming_payload,
                'outgoing_payload': result
            },
            'logs': result
        }


type_to_class = {
    'ansible_playbook': AnsibleService,
    'rest_call': RestCallService
}

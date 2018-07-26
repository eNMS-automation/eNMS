from json import dumps, loads
from napalm import get_network_driver
from netmiko import ConnectHandler, file_transfer
from passlib.hash import cisco_type7
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

from eNMS import db
from eNMS.base.associations import (
    inner_task_script_table,
    scheduled_task_script_table
)
from eNMS.base.custom_base import CustomBase
from eNMS.base.helpers import get_obj, integrity_rollback, str_dict
from eNMS.scripts.properties import (
    boolean_properties,
    json_properties,
    list_properties,
    type_to_properties
)


class Script(CustomBase):

    __tablename__ = 'Script'

    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True)
    description = Column(String)
    type = Column(String)
    tasks = relationship(
        "ScheduledScriptTask",
        secondary=scheduled_task_script_table,
        back_populates="scripts"
    )
    inner_tasks = relationship(
        "InnerTask",
        secondary=inner_task_script_table,
        back_populates="scripts"
    )

    __mapper_args__ = {
        'polymorphic_identity': 'Script',
        'polymorphic_on': type
    }

    @property
    def properties(self):
        return {p: str(getattr(self, p)) for p in type_to_properties[self.type]}

    @property
    def serialized(self):
        properties = self.properties
        for prop in ('tasks', 'inner_tasks'):
            properties[prop] = [obj.properties for obj in getattr(self, prop)]
        return properties


class NetmikoConfigScript(Script):

    __tablename__ = 'NetmikoConfigScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)
    vendor = Column(String)
    operating_system = Column(String)
    content = Column(String)
    driver = Column(String)
    global_delay_factor = Column(Float)
    netmiko_type = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'netmiko_config',
    }

    def job(self, args):
        task, node, results = args
        try:
            netmiko_handler = ConnectHandler(
                device_type=self.driver,
                ip=node.ip_address,
                username=task.user.name,
                password=cisco_type7.decode(task.user.password),
                secret=node.secret_password
            )
            if self.netmiko_type == 'configuration':
                netmiko_handler.send_config_set(self.content.splitlines())
                result = 'configuration OK:\n\n{}'.format(self.content)
            else:
                # script_type is 'show_commands':
                outputs = []
                for show_command in self.content.splitlines():
                    outputs.append(netmiko_handler.send_command(show_command))
                result = '\n\n'.join(outputs)
            success = True
        except Exception as e:
            result = 'netmiko config did not work because of {}'.format(e)
            success = False
        try:
            netmiko_handler.disconnect()
        except Exception:
            pass
        results[node.name] = {'success': success, 'logs': result}


class FileTransferScript(Script):

    __tablename__ = 'FileTransferScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)
    vendor = Column(String)
    operating_system = Column(String)
    driver = Column(String)
    source_file = Column(String)
    dest_file = Column(String)
    file_system = Column(String)
    direction = Column(String)
    overwrite_file = Column(Boolean)
    disable_md5 = Column(Boolean)
    inline_transfer = Column(Boolean)

    __mapper_args__ = {
        'polymorphic_identity': 'file_transfer',
    }

    def job(self, args):
        task, node, results = args
        try:
            netmiko_handler = ConnectHandler(
                device_type=self.driver,
                ip=node.ip_address,
                username=task.user.name,
                password=cisco_type7.decode(task.user.password),
                secret=node.secret_password
            )
            transfer_dict = file_transfer(
                netmiko_handler,
                source_file=self.source_file,
                dest_file=self.dest_file,
                file_system=self.file_system,
                direction=self.direction,
                overwrite_file=self.overwrite_file,
                disable_md5=self.disable_md5,
                inline_transfer=self.inline_transfer
            )
            result = transfer_dict
            success = True
            netmiko_handler.disconnect()
        except Exception as e:
            result = 'netmiko config did not work because of {}'.format(e)
            success = False
        results[node.name] = {'success': success, 'logs': result}


class NetmikoValidationScript(Script):

    __tablename__ = 'NetmikoValidationScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)
    vendor = Column(String)
    operating_system = Column(String)
    driver = Column(String)
    command1 = Column(String)
    command2 = Column(String)
    command3 = Column(String)
    pattern1 = Column(String)
    pattern2 = Column(String)
    pattern3 = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'netmiko_validation',
    }

    def job(self, args):
        task, node, results = args
        success, outputs = True, {}
        try:
            netmiko_handler = ConnectHandler(
                device_type=self.driver,
                ip=node.ip_address,
                username=task.user.name,
                password=cisco_type7.decode(task.user.password),
                secret=node.secret_password
            )
            for i in range(1, 4):
                command = getattr(self, 'command' + str(i))
                if not command:
                    continue
                output = netmiko_handler.send_command(command)
                pattern = getattr(self, 'pattern' + str(i))
                result = 'Output: {}\n\nExpected pattern: {}'.format(output, pattern)
                outputs[command] = result
                if pattern not in output:
                    success = False
        except Exception as e:
            results[node.name] = 'netmiko did not work because of {}'.format(e)
            success = False
        result = outputs
        try:
            netmiko_handler.disconnect()
        except Exception:
            pass
        results[node.name] = {'success': success, 'logs': result}


class NapalmConfigScript(Script):

    __tablename__ = 'NapalmConfigScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)
    vendor = Column(String)
    operating_system = Column(String)
    action = Column(String)
    content = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'napalm_config',
    }

    def job(self, args):
        task, node, results = args
        try:
            driver = get_network_driver(node.operating_system)
            napalm_driver = driver(
                hostname=node.ip_address,
                username=task.user.name,
                password=cisco_type7.decode(task.user.password),
                optional_args={'secret': node.secret_password}
            )
            napalm_driver.open()
            config = '\n'.join(self.content.splitlines())
            getattr(napalm_driver, self.action)(config=config)
            napalm_driver.commit_config()
            napalm_driver.close()
        except Exception as e:
            result = 'napalm config did not work because of {}'.format(e)
            success = False
        else:
            result = 'configuration OK:\n\n{}'.format(config)
            success = True
        results[node.name] = {'success': success, 'logs': result}


class NapalmActionScript(Script):

    __tablename__ = 'NapalmActionScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)
    vendor = Column(String)
    operating_system = Column(String)
    action = Column(String, unique=True)

    __mapper_args__ = {
        'polymorphic_identity': 'napalm_action',
    }

    def __init__(self, name, action):
        self.name = name
        self.action = action

    def job(self, args):
        task, node, results = args
        try:
            driver = get_network_driver(node.operating_system)
            napalm_driver = driver(
                hostname=node.ip_address,
                username=task.user.name,
                password=cisco_type7.decode(task.user.password),
                optional_args={'secret': node.secret_password}
            )
            napalm_driver.open()
            getattr(napalm_driver, self.action)()
            napalm_driver.close()
        except Exception as e:
            result = 'napalm {} did not work because of {}'.format(self.action, e)
            success = False
        else:
            result = self.action + ' OK'
            success = True
        results[node.name] = {'success': success, 'logs': result}


class NapalmGettersScript(Script):

    __tablename__ = 'NapalmGettersScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)
    getters = Column(MutableList.as_mutable(PickleType), default=[])

    __mapper_args__ = {
        'polymorphic_identity': 'napalm_getters',
    }

    def job(self, args):
        task, node, results = args
        result = {}
        try:
            driver = get_network_driver(node.operating_system)
            napalm_driver = driver(
                hostname=node.ip_address,
                username=task.user.name,
                password=cisco_type7.decode(task.user.password),
                optional_args={'secret': node.secret_password}
            )
            napalm_driver.open()
            for getter in self.getters:
                try:
                    result[getter] = getattr(napalm_driver, getter)()
                    print(result[getter], type(result[getter]))
                except Exception as e:
                    result[getter] = '{} could not be retrieve because of {}'.format(getter, e)
            napalm_driver.close()
        except Exception as e:
            result['error'] = 'getters process did not work because of {}'.format(e)
            success = False
        else:
            success = True
        print(result)
        results[node.name] = {'success': success, 'logs': result}


class AnsibleScript(Script):

    __tablename__ = 'AnsibleScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)
    vendor = Column(String)
    operating_system = Column(String)
    playbook_path = Column(String)
    arguments = Column(String)
    graphical_inventory = Column(Boolean)
    options = Column(MutableDict.as_mutable(PickleType), default={})

    __mapper_args__ = {
        'polymorphic_identity': 'ansible_playbook',
    }

    def job(self, args):
        _, node, results = args
        arguments = self.arguments.split()
        command = ['ansible-playbook']
        if self.graphical_inventory:
            command.extend(['-i', node.ip_address + ","])
        command.append(self.playbook_path)
        results[node.name] = {'success': True, 'logs': check_output(command + arguments)}


class RestCallScript(Script):

    __tablename__ = 'RestCallScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)
    call_type = Column(String)
    url = Column(String)
    payload = Column(MutableDict.as_mutable(PickleType), default={})
    content = Column(String)
    content_regex = Column(Boolean)
    username = Column(String)
    password = Column(String)

    request_dict = {
        'GET': rest_get,
        'POST': rest_post,
        'PUT': rest_put,
        'DELETE': rest_delete
    }

    __mapper_args__ = {
        'polymorphic_identity': 'rest_call',
    }

    def job(self, args):
        _, node, results = args
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
            if self.content_regex:
                success = bool(search(self.content, str(result)))
            else:
                success = self.content in str(result)
        except Exception as e:
            result, success = str(e), False
        results[node.name] = {'success': success, 'logs': result}


type_to_class = {
    'napalm_action': NapalmActionScript,
    'netmiko_config': NetmikoConfigScript,
    'netmiko_validation': NetmikoValidationScript,
    'napalm_config': NapalmConfigScript,
    'file_transfer': FileTransferScript,
    'napalm_getters': NapalmGettersScript,
    'ansible_playbook': AnsibleScript,
    'rest_call': RestCallScript
}


def script_factory(type, **kwargs):
    cls = type_to_class[type]
    script = get_obj(cls, name=kwargs['name'][0]) or cls()
    print(kwargs)
    for property in type_to_properties[type]:
        # type is not in kwargs, we leave it unchanged
        if property not in kwargs:
            continue
        # unchecked tickbox do not yield any value when posting a form, and
        # they yield "y" if checked
        if property in boolean_properties:
            value = property in kwargs
        elif property in json_properties:
            str_dict, = kwargs[property]
            value = loads(str_dict) if str_dict else {}
        # if the property is not a list, we unpack it as it is returned
        # as a singleton in the ImmutableMultiDict
        elif property not in list_properties:
            value, = kwargs[property]
        else:
            value = kwargs[property]
        setattr(script, property, value)
    db.session.commit()
    return script


default_scripts = (
    ('NAPALM Rollback', 'rollback'),
)


@integrity_rollback
def create_default_scripts():
    for name, action in default_scripts:
        script = NapalmActionScript(name, action)
        db.session.add(script)
        db.session.commit()

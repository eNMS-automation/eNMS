from napalm import get_network_driver
from netmiko import ConnectHandler, file_transfer
from passlib.hash import cisco_type7
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
from eNMS.base.helpers import get_obj, integrity_rollback, str_dict
from eNMS.base.models import (
    inner_task_script_table,
    scheduled_task_script_table,
    CustomBase
)
from eNMS.base.properties import cls_to_properties
from eNMS.scripts.properties import (
    boolean_properties,
    list_properties,
    type_to_properties
)


class Script(CustomBase):

    __tablename__ = 'Script'

    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True)
    description = Column(String)
    waiting_time = Column(Integer)
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

    def __init__(self, name, waiting_time=0, description=''):
        self.name = name
        self.waiting_time = waiting_time
        self.description = description

    @property
    def serialized(self):
        return {p: getattr(self, p) for p in cls_to_properties['Script']}

    def script_neighbors(self, workflow, type):
        return [
            x.destination for x in self.destinations
            if x.workflow == workflow and x.type == type
        ]


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

    def __init__(self, real_content, **data):
        name = data['name'][0]
        waiting_time = data['waiting_time'][0]
        description = data['description'][0]
        self.vendor = data['vendor'][0]
        self.operating_system = data['operating_system'][0]
        self.driver = data['driver'][0]
        self.global_delay_factor = data['global_delay_factor'][0]
        self.netmiko_type = data['netmiko_type'][0]
        super(NetmikoConfigScript, self).__init__(name, waiting_time, description)
        self.content = ''.join(real_content)

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
                result = 'configuration OK'
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
        results[node.name] = result
        return success


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

    def __init__(self, source_file_path, **data):
        name = data['name'][0]
        waiting_time = data['waiting_time'][0]
        description = data['description'][0]
        self.vendor = data['vendor'][0]
        self.operating_system = data['operating_system'][0]
        self.source_file = source_file_path
        self.driver = data['driver'][0]
        self.dest_file = data['dest_file'][0]
        self.file_system = data['file_system'][0]
        self.direction = data['direction'][0]
        for property in ('overwrite_file', 'disable_md5', 'inline_transfer'):
            setattr(self, property, property in data)
        super(FileTransferScript, self).__init__(name, waiting_time, description)

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
            result = str(transfer_dict)
            success = True
            netmiko_handler.disconnect()
        except Exception as e:
            result = 'netmiko config did not work because of {}'.format(e)
            success = False
        results[node.name] = result
        return success


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

    def __init__(self, **data):
        name = data['name'][0]
        waiting_time = data['waiting_time'][0]
        description = data['description'][0]
        self.vendor = data['vendor'][0]
        self.operating_system = data['operating_system'][0]
        self.driver = data['driver'][0]
        for i in range(1, 4):
            for property in ('command', 'pattern'):
                setattr(self, property + str(i), data[property + str(i)][0])
        super(NetmikoValidationScript, self).__init__(name, waiting_time, description)

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
        results[node.name] = str_dict(outputs)
        try:
            netmiko_handler.disconnect()
        except Exception:
            pass
        return success


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

    def __init__(self, real_content, **data):
        name = data['name'][0]
        waiting_time = data['waiting_time'][0]
        description = data['description'][0]
        super(NapalmConfigScript, self).__init__(name, waiting_time, description)
        self.vendor = data['vendor'][0]
        self.operating_system = data['operating_system'][0]
        self.content = ''.join(real_content)
        self.action = data['action'][0]

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
            if self.action in ('load_merge_candidate', 'load_replace_candidate'):
                getattr(napalm_driver, self.action)(config=self.content)
            else:
                getattr(napalm_driver, self.action)()
            napalm_driver.close()
        except Exception as e:
            result = 'napalm config did not work because of {}'.format(e)
            success = False
        else:
            result = 'configuration OK'
            success = True
        results[node.name] = result
        return success


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
        self.action = action
        super(NapalmActionScript, self).__init__(name)

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
        results[node.name] = result
        return success


class NapalmGettersScript(Script):

    __tablename__ = 'NapalmGettersScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)
    vendor = Column(String)
    operating_system = Column(String)
    getters = Column(MutableList.as_mutable(PickleType), default=[])

    __mapper_args__ = {
        'polymorphic_identity': 'napalm_getters',
    }

    def __init__(self, **data):
        name = data['name'][0]
        waiting_time = data['waiting_time'][0]
        description = data['description'][0]
        self.getters = data['getters']
        super(NapalmGettersScript, self).__init__(name, waiting_time, description)

    def job(self, args):
        task, node, results = args
        dict_result = {}
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
                    dict_result[getter] = str_dict(getattr(napalm_driver, getter)())
                except Exception as e:
                    dict_result[getter] = '{} could not be retrieve because of {}'.format(getter, e)
            napalm_driver.close()
        except Exception as e:
            dict_result['error'] = 'getters process did not work because of {}'.format(e)
            success = False
        else:
            success = True
            results[node.name] = dict_result
        return success


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

    def __init__(self, **data):
        name = data['name'][0]
        waiting_time = data['waiting_time'][0]
        description = data['description'][0]
        self.vendor = data['vendor'][0]
        self.operating_system = data['operating_system'][0]
        self.playbook_path = data['playbook_path'][0]
        self.arguments = data['arguments'][0]
        self.graphical_inventory = 'graphical_inventory' in data
        super(AnsibleScript, self).__init__(name, waiting_time, description)

    def job(self, args):
        _, node, results = args
        arguments = self.arguments.split()
        command = ['ansible-playbook']
        if self.graphical_inventory:
            command.extend(['-i', node.ip_address + ","])
        command.append(self.playbook_path)
        results[node.name] = check_output(command + arguments)
        return True


type_to_class = {
    'napalm_action': NapalmActionScript,
    'netmiko_config': NetmikoConfigScript,
    'netmiko_validation': NetmikoValidationScript,
    'napalm_config': NapalmConfigScript,
    'file_transfer': FileTransferScript,
    'napalm_getters': NapalmGettersScript,
    'ansible_playbook': AnsibleScript,
}


def script_factory(type, **kwargs):
    cls = type_to_class[type]
    script = get_obj(cls, name=kwargs['name'][0])
    for property in type_to_properties[type]:
        # type is not in kwargs, we leave it unchanged
        if property not in kwargs:
            continue
        # unchecked tickbox do not yield any value when posting a form, and
        # they yield "y" if checked
        if property in boolean_properties:
            value = property in kwargs
        # if the property is not a list, we unpack it as it is returned
        # as a singleton in the ImmutableMultiDict
        elif property not in list_properties:
            value, = kwargs[property]
        else:
            value = kwargs[property]
        setattr(script, property, value)
    db.session.commit()


default_scripts = (
    ('NAPALM Commit', 'commit_config'),
    ('NAPALM Discard', 'discard_config'),
    ('NAPALM Rollback', 'rollback')
)


@integrity_rollback
def create_default_scripts():
    for name, action in default_scripts:
        script = NapalmActionScript(name, action)
        db.session.add(script)
        db.session.commit()

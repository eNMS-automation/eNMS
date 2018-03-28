from tempfile import NamedTemporaryFile
from base.database import db
from base.helpers import str_dict
from base.models import CustomBase
from collections import namedtuple
from datetime import datetime, timedelta
from flask_apscheduler import APScheduler
from multiprocessing.pool import ThreadPool
from netmiko import ConnectHandler
from passlib.hash import cisco_type7
from scripts.models import AnsibleScript, ConfigScript
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, PickleType
from sqlalchemy.ext.mutable import MutableDict, MutableList

# napalm pre and post-reunification compatibility
try:
    from napalm import get_network_driver
except ImportError:
    from napalm_base import get_network_driver

try:
    from ansible.parsing.dataloader import DataLoader
    from ansible.vars.manager import VariableManager
    from ansible.inventory.manager import InventoryManager
    from ansible.executor.playbook_executor import PlaybookExecutor
except Exception:
    import warnings
    warnings.warn('ansible import failed: ansible feature deactivated')

scheduler = APScheduler()

## Netmiko process and job


def netmiko_config_job(name, type, script_name, username, password, ips, driver,
                       global_delay_factor):
    job_time = str(datetime.now())
    task = db.session.query(Task)\
        .filter_by(name=name)\
        .first()
    script = db.session.query(ConfigScript)\
        .filter_by(name=script_name)\
        .first()
    pool = ThreadPool(processes=10)
    results = {}
    kwargs = [({
        'ip': ip_address,
        'device_type': driver,
        'username': username,
        'password': password,
        'secret': secret,
        'global_delay_factor': global_delay_factor,
        'name': device_name,
        'results': results,
        'type': type
    }) for device_name, ip_address, _, secret in ips]
    pool.map(script.netmiko_process, kwargs)
    pool.close()
    pool.join()
    task.logs[job_time] = results
    db.session.commit()


def netmiko_file_transfer_job(name, type, script_name, username, password, ips,
                              driver, global_delay_factor):
    job_time = str(datetime.now())
    task = db.session.query(Task)\
        .filter_by(name=name)\
        .first()
    script = db.session.query(ConfigScript)\
        .filter_by(name=script_name)\
        .first()
    pool = ThreadPool(processes=10)
    results = {}
    kwargs = [({
        'ip': ip_address,
        'device_type': driver,
        'username': username,
        'password': password,
        'secret': secret,
        'global_delay_factor': global_delay_factor,
        'name': device_name,
        'source_file': script.source_file,
        'dest_file': script.destination_file,
        'file_system': script.file_system,
        'direction': script.direction,
        'results': results,
        'type': type
    }) for device_name, ip_address, _, secret in ips]
    pool.map(netmiko_process, kwargs)
    pool.close()
    pool.join()
    task.logs[job_time] = results
    db.session.commit()

## Napalm processes and jobs


def napalm_config_process(kwargs):
    try:
        driver = get_network_driver(kwargs['driver'])
        napalm_driver = driver(
            hostname=kwargs['ip_address'],
            username=kwargs['username'],
            password=kwargs['password'],
            optional_args={'secret': kwargs['secret']}
        )
        napalm_driver.open()
        if kwargs['action'] in ('load_merge_candidate', 'load_replace_candidate'):
            getattr(napalm_driver, kwargs['action'])(config=kwargs['script'])
        else:
            getattr(napalm_driver, kwargs['action'])()
        napalm_driver.close()
    except Exception as e:
        result = 'napalm config did not work because of {}'.format(e)
    else:
        result = 'configuration OK'
    kwargs['results'][kwargs['name']] = result


def napalm_config_job(name, script_name, username, password, nodes_info, action):
    job_time = str(datetime.now())
    task = db.session.query(Task)\
        .filter_by(name=name)\
        .first()
    script = db.session.query(ConfigScript)\
        .filter_by(name=script_name)\
        .first()
    pool = ThreadPool(processes=10)
    results = {}
    kwargs = [({
        'action': action,
        'ip_address': ip_address,
        'driver': driver,
        'username': username,
        'password': password,
        'secret': secret,
        'name': device_name,
        'script': script.content,
        'results': results
    }) for device_name, ip_address, driver, secret in nodes_info]
    pool.map(napalm_config_process, kwargs)
    pool.close()
    pool.join()
    task.logs[job_time] = results
    db.session.commit()


def napalm_getters_process(kwargs):
    try:
        driver = get_network_driver(kwargs['driver'])
        napalm_driver = driver(
            hostname=kwargs['ip_address'],
            username=kwargs['username'],
            password=kwargs['password'],
            optional_args={'secret': kwargs['secret']}
        )
        napalm_driver.open()
        for getter in kwargs['getters']:
            try:
                result = str_dict(getattr(napalm_driver, getter)())
            except Exception as e:
                result = '{} could not be retrieve because of {}'.format(getter, e)
        napalm_driver.close()
    except Exception as e:
        result = 'getters process did not work because of {}'.format(e)
    kwargs['results'][kwargs['name']] = result


def napalm_getters_job(name, getters, username, password, nodes_info):
    job_time = str(datetime.now())
    task = db.session.query(Task)\
        .filter_by(name=name)\
        .first()
    pool = ThreadPool(processes=10)
    results = {}
    kwargs = [({
        'ip_address': ip_address,
        'driver': driver,
        'username': username,
        'password': password,
        'secret': secret,
        'name': device_name,
        'getters': getters,
        'results': results
    }) for device_name, ip_address, driver, secret in nodes_info]
    pool.map(napalm_getters_process, kwargs)
    pool.close()
    pool.join()
    task.logs[job_time] = results
    db.session.commit()


def ansible_job(name, script_name, username, password, nodes_info):
    job_time = str(datetime.now())
    task = db.session.query(Task)\
        .filter_by(name=name)\
        .first()
    script = db.session.query(AnsibleScript)\
        .filter_by(name=script_name)\
        .first()
    loader = DataLoader()
    hosts = [info[1] for info in nodes_info]
    temporary_file = NamedTemporaryFile(delete=False)
    temporary_file.write('\n'.join(hosts))
    temporary_file.close()

    # sources is a list of paths to inventory files"
    inventory = InventoryManager(loader=loader, sources=temporary_file.name)
    variable_manager = VariableManager(loader=loader, inventory=inventory)
    playbook_path = script.playbook_path

    options_dict = {
        'listtags': False,
        'listtasks': False,
        'listhosts': False,
        'syntax': False,
        'connection': 'ssh',
        'module_path': None,
        'forks': 100,
        'remote_user': None,
        'private_key_file': None,
        'ssh_common_args': None,
        'ssh_extra_args': None,
        'sftp_extra_args': None,
        'scp_extra_args': None,
        'become': False,
        'become_method': None,
        'become_user': None,
        'verbosity': None,
        'check': False,
        'diff': False
    }

    Options = namedtuple('Options', list(options_dict))
    passwords = {}
    playbook_executor = PlaybookExecutor(
        playbooks=[playbook_path],
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        options=Options(**options_dict),
        passwords=passwords
    )

    results = playbook_executor.run()
    task.logs[job_time] = results
    db.session.commit()

## Tasks


class Task(CustomBase):

    __tablename__ = 'Task'

    id = Column(Integer, primary_key=True)
    type = Column(String)
    recurrent = Column(Boolean, default=False)
    name = Column(String(120), unique=True)
    status = Column(String)
    creation_time = Column(Integer)
    logs = Column(MutableDict.as_mutable(PickleType), default={})
    nodes = Column(MutableList.as_mutable(PickleType), default=[])

    # scheduling parameters
    frequency = Column(String(120))
    start_date = Column(String)
    end_date = Column(String)

    # script parameters
    creator = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'Task',
        'polymorphic_on': type
    }

    def __init__(self, user, **data):
        self.name = data['name']
        self.frequency = data['frequency']
        self.recurrent = bool(data['frequency'])
        self.creation_time = str(datetime.now())
        self.creator = user.username
        self.status = 'active'
        # if the start date is left empty, we turn the empty string into
        # None as this is what AP Scheduler is expecting
        for date in ('start_date', 'end_date'):
            value = self.datetime_conversion(data[date]) if data[date] else None
            setattr(self, date, value)
        self.is_active = True
        if data['frequency']:
            self.recurrent_scheduling()
        else:
            self.one_time_scheduling()

    @property
    def description(self):
        return '\n'.join([
            'Name: ' + self.name,
            'Frequency: {}s'.format(self.frequency),
            'Creation time: ' + self.creation_time,
            'Creator: ' + self.creator
        ])

    def datetime_conversion(self, date):
        dt = datetime.strptime(date, '%d/%m/%Y %H:%M:%S')
        return datetime.strftime(dt, '%Y-%m-%d %H:%M:%S')

    def pause_task(self):
        scheduler.pause_job(self.creation_time)
        self.status = 'suspended'
        db.session.commit()

    def resume_task(self):
        scheduler.resume_job(self.creation_time)
        self.status = "active"
        db.session.commit()

    def delete_task(self):
        scheduler.delete_job(self.creation_time)
        db.session.commit()

    def recurrent_scheduling(self):
        if not self.start_date:
            self.start_date = datetime.now() + timedelta(seconds=15)
        # run the job on a regular basis with an interval trigger
        scheduler.add_job(
            id=self.creation_time,
            func=self.job,
            args=self.args,
            trigger='interval',
            start_date=self.start_date,
            end_date=self.end_date,
            seconds=int(self.frequency),
            replace_existing=True
        )

    def one_time_scheduling(self):
        if not self.start_date:
            # when the job is scheduled to run immediately, it may happen that
            # the job is run even before the task is created, in which case
            # it fails because it cannot be retrieve from the Task column of
            # the database: we introduce a delta of 5 seconds.
            # other situation: the server is too slow and the job cannot be
            # run at all, eg 'job was missed by 0:00:09.465684'
            self.start_date = datetime.now() + timedelta(seconds=5)
        # execute the job immediately with a date-type job
        # when date is used as a trigger and run_date is left undetermined,
        # the job is executed immediately.
        scheduler.add_job(
            id=self.creation_time,
            run_date=self.start_date,
            func=self.job,
            args=self.args,
            trigger='date'
        )


class NetmikoConfigTask(Task):

    __tablename__ = 'NetmikoConfigTask'

    id = Column(Integer, ForeignKey('Task.id'), primary_key=True)
    script = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'NetmikoConfigTask',
    }

    def __init__(self, user, targets, **data):
        self.subtype = data['type']
        self.script_name = data['script']
        self.user = user
        self.nodes = targets
        self.data = data
        self.job = netmiko_config_job
        self.args = [
            data['name'],
            data['type'],
            self.script_name,
            self.user.username,
            cisco_type7.decode(self.user.password),
            targets,
            data['driver'],
            data['global_delay_factor']
        ]
        super(NetmikoConfigTask, self).__init__(user, **data)


class NetmikoFileTransferTask(Task):

    __tablename__ = 'NetmikoFileTransferTask'

    id = Column(Integer, ForeignKey('Task.id'), primary_key=True)
    script = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'NetmikoFileTransferTask',
    }

    def __init__(self, user, targets, **data):
        self.subtype = 'file_transfer'
        self.script_name = data['script']
        self.user = user
        self.nodes = targets
        self.data = data
        self.job = netmiko_file_transfer_job
        self.args = [
            data['name'],
            self.script_name,
            self.user.username,
            cisco_type7.decode(self.user.password),
            targets,
            data['driver'],
            data['global_delay_factor']
        ]
        super(NetmikoFileTransferTask, self).__init__(user, **data)


class NapalmConfigTask(Task):

    __tablename__ = 'NapalmConfigTask'

    id = Column(Integer, ForeignKey('Task.id'), primary_key=True)
    script = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'NapalmConfigTask',
    }

    def __init__(self, user, targets, **data):
        self.subtype = 'napalm_config'
        self.script_name = data['script']
        self.user = user
        self.nodes = targets
        self.data = data
        self.job = napalm_config_job
        self.args = [
            data['name'],
            self.script_name,
            self.user.username,
            cisco_type7.decode(self.user.password),
            targets,
            data['actions']
        ]
        super(NapalmConfigTask, self).__init__(user, **data)


class NapalmGettersTask(Task):

    __tablename__ = 'NapalmGettersTask'

    id = Column(Integer, ForeignKey('Task.id'), primary_key=True)
    script = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'NapalmGettersTask',
    }

    def __init__(self, user, targets, **data):
        self.subtype = 'napalm_getters'
        self.user = user
        self.nodes = targets
        self.data = data
        self.job = napalm_getters_job
        self.args = [
            data['name'],
            data['getters'],
            self.user.username,
            cisco_type7.decode(self.user.password),
            targets
        ]
        super(NapalmGettersTask, self).__init__(user, **data)


class AnsibleTask(Task):

    __tablename__ = 'AnsibleTask'

    id = Column(Integer, ForeignKey('Task.id'), primary_key=True)
    script = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'AnsibleTask',
    }

    def __init__(self, user, targets, **data):
        self.subtype = 'ansible'
        self.script_name = data['script']
        self.user = user
        self.nodes = targets
        self.data = data
        self.job = ansible_job
        self.args = [
            data['name'],
            self.script_name,
            self.user.username,
            cisco_type7.decode(self.user.password),
            targets
        ]
        super(AnsibleTask, self).__init__(user, **data)

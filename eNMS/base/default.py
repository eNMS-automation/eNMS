from os.path import join
from xlrd import open_workbook
from xlrd.biffh import XLRDError

from eNMS import db
from eNMS.admin.models import Parameters, SyslogServer, User
from eNMS.base.custom_base import factory
from eNMS.base.helpers import integrity_rollback, retrieve
from eNMS.objects.models import Device, Pool
from eNMS.objects.routes import process_kwargs
from eNMS.scripts.models import NetmikoConfigScript, Script
from eNMS.tasks.models import ScriptTask


def create_default_user():
    user = factory(User, **{
        'name': 'cisco',
        'email': 'cisco@cisco.com',
        'password': 'cisco'
    })


def create_default_pools():
    for pool in (
        {'name': 'All objects'},
        {'name': 'Devices only', 'link_name': '^$', 'link_name_regex': True},
        {'name': 'Links only', 'device_name': '^$', 'device_name_regex': True}
    ):
        factory(Pool, **pool)


@integrity_rollback
def create_default_parameters():
    parameters = Parameters()
    db.session.add(parameters)
    db.session.commit()


@integrity_rollback
def create_default_syslog_server():
    syslog_server = SyslogServer(ip_address='0.0.0.0', port=514)
    db.session.add(syslog_server)
    db.session.commit()


@integrity_rollback
def create_default_network_topology(app):
    with open(join(app.path, 'projects', 'defaults.xls'), 'rb') as f:
        book = open_workbook(file_contents=f.read())
        for object_type in ('Device', 'Link'):
            try:
                sheet = book.sheet_by_name(object_type)
            except XLRDError:
                continue
            properties = sheet.row_values(0)
            for row_index in range(1, sheet.nrows):
                values = dict(zip(properties, sheet.row_values(row_index)))
                cls, kwargs = process_kwargs(app, **values)
                factory(cls, **kwargs).serialized
            db.session.commit()


def create_default_scripts():
    for script in (
        {
            'name': 'create_vrf_TEST',
            'description': 'Create a VRF "TEST"',
            'vendor': 'Cisco',
            'operating_system': 'IOS',
            'content_type': 'simple',
            'driver': 'cisco_ios',
            'global_delay_factor': '1.0',
            'content': 'ip vrf TEST'
        },
        {
            'name': 'delete_vrf_TEST',
            'description': 'Delete VRF "TEST"',
            'vendor': 'Cisco',
            'operating_system': 'IOS',
            'content_type': 'simple',
            'driver': 'cisco_ios',
            'global_delay_factor': '1.0',
            'content': 'no ip vrf TEST'
        }
    ):
        factory(NetmikoConfigScript, **script)


def create_default_tasks():
    for task in (
        {
            'name': 'task_create_vrf_TEST',
            'waiting_time': '0',
            'devices': [retrieve(Device, name='router8')],
            'job': retrieve(Script, name='create_vrf_TEST'),
            'start_date': '',
            'end_date': '',
            'frequency': '',
            'do_not_run': 'y',
            'user': retrieve(User, name='cisco')
        },
        {
            'name': 'task_delete_vrf_TEST',
            'waiting_time': '0',
            'devices': [retrieve(Device, name='router8')],
            'job': retrieve(Script, name='delete_vrf_TEST'),
            'start_date': '',
            'end_date': '',
            'frequency': '',
            'do_not_run': 'y',
            'user': retrieve(User, name='cisco')
        }
    ):
        factory(ScriptTask, **task)

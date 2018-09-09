from os.path import join
from xlrd import open_workbook
from xlrd.biffh import XLRDError

from eNMS import db
from eNMS.admin.models import Parameters, SyslogServer, User
from eNMS.base.custom_base import factory
from eNMS.base.helpers import integrity_rollback, retrieve
from eNMS.objects.models import Device, Pool
from eNMS.objects.routes import process_kwargs
from eNMS.scripts.models import (
    NetmikoConfigScript,
    NetmikoValidationScript,
    Script
)
from eNMS.tasks.models import ScriptTask, Task, WorkflowTask
from eNMS.workflows.models import Workflow, WorkflowEdge


def create_default_user():
    factory(User, **{
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
            'type': NetmikoConfigScript,
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
            'type': NetmikoValidationScript,
            'name': 'check_vrf_TEST',
            'description': 'Check that the vrf "TEST" is configured',
            'vendor': 'Cisco',
            'operating_system': 'IOS',
            'driver': 'cisco_ios',
            'command1': 'show ip vrf',
            'content_match1': 'TEST'
        },
        {
            'type': NetmikoConfigScript,
            'name': 'delete_vrf_TEST',
            'description': 'Delete VRF "TEST"',
            'vendor': 'Cisco',
            'operating_system': 'IOS',
            'content_type': 'simple',
            'driver': 'cisco_ios',
            'global_delay_factor': '1.0',
            'content': 'no ip vrf TEST'
        },
        {
            'type': NetmikoValidationScript,
            'name': 'check_no_vrf_TEST',
            'description': 'Check that the vrf "TEST" is NOT configured',
            'vendor': 'Cisco',
            'operating_system': 'IOS',
            'driver': 'cisco_ios',
            'command1': 'show ip vrf',
            'content_match1': '^((?!gegr).)*$',
            'content_match_regex1': 'y'
        },
    ):
        factory(script.pop('type'), **script)


def create_default_tasks():
    dev, user = retrieve(Device, name='router8'), retrieve(User, name='cisco')
    scripts = [
        retrieve(Script, name=script_name) for script_name in (
            'create_vrf_TEST',
            'check_vrf_TEST',
            'delete_vrf_TEST',
            'check_no_vrf_TEST'
        )
    ]
    for script in scripts:
        factory(ScriptTask, **{
            'name': f'task_{script.name}',
            'devices': [dev],
            'job': script,
            'do_not_run': 'y',
            'user': user
        })


def create_default_workflows():
    tasks = [
        retrieve(Task, name=task_name) for task_name in (
            'task_create_vrf_TEST',
            'task_check_vrf_TEST',
            'task_delete_vrf_TEST',
            'task_check_no_vrf_TEST'
        )
    ]
    workflow = factory(Workflow, **{
        'name': 'Netmiko_VRF_workflow',
        'description': 'Create and delete a VRF with Netmiko',
        'tasks': tasks
    })
    for i in range(len(tasks) - 1):
        factory(WorkflowEdge, **{
            'name': f'{tasks[i].name} -> {tasks[i + 1].name}',
            'workflow': workflow,
            'type': 'success',
            'source': tasks[i],
            'destination': tasks[i + 1]
        })
    workflow.start_task = tasks[0].id
    workflow_task = factory(WorkflowTask, **{
        'name': 'task_netmiko_VRF_workflow',
        'job': workflow,
        'do_not_run': 'y',
        'user': retrieve(User, name='cisco')
    })

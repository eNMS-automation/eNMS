from importlib.util import spec_from_file_location, module_from_spec
from os.path import join
from pathlib import Path
from sqlalchemy import Boolean, Float, Integer, PickleType
from xlrd import open_workbook
from xlrd.biffh import XLRDError

from eNMS import db
from eNMS.admin.models import Parameters, User
from eNMS.base.custom_base import factory
from eNMS.base.helpers import integrity_rollback, retrieve
from eNMS.base.properties import property_types
from eNMS.objects.models import Device, Pool
from eNMS.objects.routes import process_kwargs
from eNMS.services.models import Job, service_classes
from eNMS.tasks.models import ServiceTask, Task, WorkflowTask
from eNMS.workflows.models import Workflow, WorkflowEdge


@integrity_rollback
def create_service_classes():
    path_services = Path.cwd() / 'eNMS' / 'services' / 'services'
    for file in path_services.glob('**/*.py'):
        if 'init' not in str(file):
            spec = spec_from_file_location(str(file), str(file))
            spec.loader.exec_module(module_from_spec(spec))
    for cls_name, cls in service_classes.items():
        for col in cls.__table__.columns:
            if (
                type(col.type) == PickleType and
                hasattr(cls, f'{col.key}_values')
            ):
                property_types[col.key] = list
            else:
                property_types[col.key] = {
                    Boolean: bool,
                    Integer: int,
                    Float: float,
                    PickleType: dict,
                }.get(type(col.type), str)


def create_default_users():
    factory(User, **{
        'name': 'admin',
        'email': 'admin@admin.com',
        'password': 'admin',
        'permissions': ['Admin']
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


@integrity_rollback
def create_default_services():
    for service in (
        {
            'type': service_classes['Configure Bgp Service'],
            'name': 'napalm_configure_bgp_1',
            'description': 'Configure BGP Peering with Napalm',
            'devices': [retrieve(Device, name='router8')],
            'local_as': 100,
            'loopback': 'Lo100',
            'loopback_ip': '100.1.1.1',
            'neighbor_ip': '100.1.2.1',
            'remote_as': 200,
            'vrf_name': 'configure_BGP_test',
            'waiting_time': 0
        },
    ):
        instance = factory(service.pop('type'), **service)
        factory(ServiceTask, **{
            'name': f'task_{instance.name}',
            'start-task': 'do-not-run',
            'job': instance,
            'user': retrieve(User, name='admin')
        })


@integrity_rollback
def create_netmiko_workflow():
    services = []
    for service in (
        {
            'type': service_classes['Netmiko Configuration Service'],
            'name': 'netmiko_create_vrf_TEST',
            'description': 'Create a VRF "TEST" with Netmiko',
            'waiting_time': 0,
            'devices': [retrieve(Device, name='router8')],
            'vendor': 'Cisco',
            'operating_system': 'IOS',
            'driver': 'cisco_ios',
            'global_delay_factor': '1.0',
            'content': 'ip vrf TEST'
        },
        {
            'type': service_classes['Netmiko Validation Service'],
            'name': 'netmiko_check_vrf_TEST',
            'description': 'Check that the vrf "TEST" is configured',
            'waiting_time': 0,
            'devices': [retrieve(Device, name='router8')],
            'vendor': 'Cisco',
            'operating_system': 'IOS',
            'driver': 'cisco_ios',
            'command1': 'show ip vrf',
            'content_match1': 'TEST'
        },
        {
            'type': service_classes['Netmiko Configuration Service'],
            'name': 'netmiko_delete_vrf_TEST',
            'description': 'Delete VRF "TEST"',
            'waiting_time': 15,
            'devices': [retrieve(Device, name='router8')],
            'vendor': 'Cisco',
            'operating_system': 'IOS',
            'driver': 'cisco_ios',
            'global_delay_factor': '1.0',
            'content': 'no ip vrf TEST'
        },
        {
            'type': service_classes['Netmiko Validation Service'],
            'name': 'netmiko_check_no_vrf_TEST',
            'description': 'Check that the vrf "TEST" is NOT configured',
            'waiting_time': 0,
            'devices': [retrieve(Device, name='router8')],
            'vendor': 'Cisco',
            'operating_system': 'IOS',
            'driver': 'cisco_ios',
            'command1': 'show ip vrf',
            'content_match1': '^((?!TEST).)*$',
            'content_match_regex1': 'y'
        },
    ):
        instance = factory(service.pop('type'), **service)
        services.append(instance)
        factory(ServiceTask, **{
            'name': f'task_{instance.name}',
            'start-task': 'do-not-run',
            'job': instance,
            'user': retrieve(User, name='admin')
        })
    workflow = factory(Workflow, **{
        'name': 'Netmiko_VRF_workflow',
        'description': 'Create and delete a VRF with Netmiko',
        'vendor': 'Cisco',
        'operating_system': 'IOS',
        'jobs': services
    })
    for i in range(len(services) - 1):
        factory(WorkflowEdge, **{
            'name': f'{services[i].name} -> {services[i + 1].name}',
            'workflow': workflow,
            'type': True,
            'source': services[i],
            'destination': services[i + 1]
        })
    workflow.start_task, workflow.end_task = services[0].id, services[-1].id
    factory(WorkflowTask, **{
        'name': 'task_netmiko_VRF_workflow',
        'start-task': 'do-not-run',
        'job': workflow,
        'user': retrieve(User, name='admin')
    })
    for index, task in enumerate(services):
        task.positions['Netmiko_VRF_workflow'] = (0, 100 * index)


@integrity_rollback
def create_napalm_workflow():
    services = []
    for service in (
        {
            'type': service_classes['Napalm Configuration Service'],
            'name': 'napalm_create_vrf_TEST',
            'description': 'Create a VRF "TEST" with Napalm',
            'waiting_time': 0,
            'devices': [retrieve(Device, name='router8')],
            'driver': 'ios',
            'vendor': 'Cisco',
            'operating_system': 'IOS',
            'content_type': 'simple',
            'action': 'load_merge_candidate',
            'content': 'ip vrf TEST'
        },
        {
            'type': service_classes['Napalm Rollback Service'],
            'name': 'Napalm IOS Rollback',
            'driver': 'ios',
            'description': 'Rollback a configuration with Napalm IOS',
            'devices': [retrieve(Device, name='router8')],
            'waiting_time': 0
        }
    ):
        instance = factory(service.pop('type'), **service)
        services.append(instance)
        factory(ServiceTask, **{
            'name': f'task_{instance.name}',
            'job': instance,
            'start-task': 'do-not-run',
            'user': retrieve(User, name='admin')
        })
    services.insert(1, retrieve(Job, name='netmiko_check_vrf_TEST'))
    services.append(retrieve(Job, name=f'netmiko_check_no_vrf_TEST'))
    workflow = factory(Workflow, **{
        'name': 'Napalm_VRF_workflow',
        'description': 'Create and delete a VRF with Napalm',
        'vendor': 'Cisco',
        'operating_system': 'IOS',
        'jobs': services
    })
    for i in range(len(services) - 1):
        factory(WorkflowEdge, **{
            'name': f'{services[i].name} -> {services[i + 1].name}',
            'workflow': workflow,
            'type': True,
            'source': services[i],
            'destination': services[i + 1]
        })
    workflow.start_task, workflow.end_task = services[0].id, services[-1].id
    factory(WorkflowTask, **{
        'name': 'task_napalm_VRF_workflow',
        'start-task': 'do-not-run',
        'job': workflow,
        'user': retrieve(User, name='admin')
    })
    for index, task in enumerate(services):
        task.positions['Napalm_VRF_workflow'] = (0, 100 * index)


def create_payload_transfer_workflow():
    services = []
    for service in [{
        'name': 'GET_router8',
        'type': service_classes['Rest Call Service'],
        'description': 'Use GET ReST call on router8',
        'waiting_time': 0,
        'devices': [retrieve(Device, name='router8')],
        'content_match': '',
        'call_type': 'GET',
        'url': 'http://127.0.0.1:5000/rest/object/device/router8',
        'payload': ''
    }] + [{
        'name': f'{getter}',
        'type': service_classes['Napalm Getters Service'],
        'description': f'Getter: {getter}',
        'waiting_time': 0,
        'devices': [retrieve(Device, name='router8')],
        'driver': 'ios',
        'content_match': '',
        'getters': [getter]
    } for getter in (
        'get_facts',
        'get_interfaces',
        'get_interfaces_ip',
        'get_config'
    )] + [{
        'name': 'process_payload1',
        'type': service_classes['Swiss Army Knife Service'],
        'description': 'Process Payload in example workflow',
        'waiting_time': 0,
        'devices': [retrieve(Device, name='router8')]
    }]:
        instance = factory(service.pop('type'), **service)
        services.append(instance)
        factory(ServiceTask, **{
            'name': f'task_{instance.name}',
            'job': instance,
            'start-task': 'do-not-run',
            'devices': [retrieve(Device, name='router8')],
            'user': retrieve(User, name='admin')
        })
    workflow = factory(Workflow, **{
        'name': 'payload_transfer_workflow',
        'description': 'ReST call, Napalm getters, etc',
        'vendor': 'Cisco',
        'operating_system': 'IOS',
        'jobs': services
    })

    # create workflow edges with following schema:
    edges = [(0, 1), (0, 2), (1, 3), (3, 4), (4, 5), (2, 5)]
    for x, y in edges:
        factory(WorkflowEdge, **{
            'name': f'{services[x].name} -> {services[y].name}',
            'workflow': workflow,
            'type': True,
            'source': services[x],
            'destination': services[y]
        })
    workflow.start_task, workflow.end_task = services[0].id, services[-1].id
    positions = [(-5, 0), (-5, -10), (15, 10), (15, -10), (40, -10), (40, 0)]
    for index, (x, y) in enumerate(positions):
        services[index].positions['payload_transfer_workflow'] = x * 10, y * 10
    factory(WorkflowTask, **{
        'name': 'task_payload_transfer_workflow',
        'start-task': 'do-not-run',
        'job': workflow,
        'user': retrieve(User, name='admin')
    })


def create_default_workflows():
    create_default_services()
    create_netmiko_workflow()
    create_napalm_workflow()
    create_payload_transfer_workflow()

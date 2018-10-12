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
from eNMS.automation.models import Job, service_classes, Workflow, WorkflowEdge


@integrity_rollback
def create_service_classes():
    path_services = Path.cwd() / 'eNMS' / 'automation' / 'services'
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
            'type': service_classes['configure_bgp_service'],
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
        factory(service.pop('type'), **service)


@integrity_rollback
def create_netmiko_workflow():
    services = []
    for service in (
        {
            'type': service_classes['netmiko_configuration_service'],
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
            'type': service_classes['netmiko_validation_service'],
            'name': 'netmiko_check_vrf_TEST',
            'description': 'Check that the vrf "TEST" is configured',
            'waiting_time': 0,
            'devices': [retrieve(Device, name='router8')],
            'vendor': 'Cisco',
            'operating_system': 'IOS',
            'driver': 'cisco_ios',
            'content': 'show ip vrf',
            'content_match': 'TEST'
        },
        {
            'type': service_classes['netmiko_configuration_service'],
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
            'type': service_classes['netmiko_validation_service'],
            'name': 'netmiko_check_no_vrf_TEST',
            'description': 'Check that the vrf "TEST" is NOT configured',
            'waiting_time': 0,
            'devices': [retrieve(Device, name='router8')],
            'vendor': 'Cisco',
            'operating_system': 'IOS',
            'driver': 'cisco_ios',
            'content': 'show ip vrf',
            'content_match': '^((?!TEST).)*$',
            'content_match_regex': 'y'
        },
    ):
        instance = factory(service.pop('type'), **service)
        services.append(instance)
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
    workflow.start_job, workflow.end_job = services[0], services[-1]
    for index, service in enumerate(services):
        service.positions['Netmiko_VRF_workflow'] = (0, 100 * index)


@integrity_rollback
def create_napalm_workflow():
    services = []
    for service in (
        {
            'type': service_classes['napalm_configuration_service'],
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
            'type': service_classes['napalm_rollback_service'],
            'name': 'Napalm IOS Rollback',
            'driver': 'ios',
            'description': 'Rollback a configuration with Napalm IOS',
            'devices': [retrieve(Device, name='router8')],
            'waiting_time': 0
        }
    ):
        instance = factory(service.pop('type'), **service)
        services.append(instance)
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
    workflow.start_job, workflow.end_job = services[0].id, services[-1].id
    for index, service in enumerate(services):
        service.positions['Napalm_VRF_workflow'] = (0, 100 * index)


def create_payload_transfer_workflow():
    services = []
    for service in [{
        'name': 'GET_router8',
        'type': service_classes['rest_call_service'],
        'description': 'Use GET ReST call on router8',
        'username': 'admin',
        'password': 'admin',
        'waiting_time': 0,
        'devices': [retrieve(Device, name='router8')],
        'content_match': '',
        'call_type': 'GET',
        'url': 'http://127.0.0.1:5000/rest/object/device/router8',
        'payload': ''
    }] + [{
        'name': f'{getter}',
        'type': service_classes['napalm_getters_service'],
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
        'type': service_classes['swiss_army_knife_service'],
        'description': 'Process Payload in example workflow',
        'waiting_time': 0,
        'devices': [retrieve(Device, name='router8')]
    }]:
        instance = factory(service.pop('type'), **service)
        services.append(instance)
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
    workflow.start_job, workflow.end_job = services[0].id, services[-1].id
    positions = [(-5, 0), (-5, -10), (15, 10), (15, -10), (40, -10), (40, 0)]
    for index, (x, y) in enumerate(positions):
        services[index].positions['payload_transfer_workflow'] = x * 10, y * 10


def create_default_workflows():
    create_netmiko_workflow()
    create_napalm_workflow()
    create_payload_transfer_workflow()
    create_default_services()

from os.path import join
from xlrd import open_workbook
from xlrd.biffh import XLRDError

from eNMS import db
from eNMS.base.models import classes
from eNMS.base.helpers import factory, integrity_rollback, fetch
from eNMS.base.security import process_kwargs


def create_default_users():
    factory('User', **{
        'name': 'admin',
        'email': 'admin@admin.com',
        'password': 'admin',
        'permissions': ['Admin']
    })


def create_default_pools():
    for pool in (
        {
            'name': 'All objects',
            'description': 'All objects'
        },
        {
            'name': 'Devices only',
            'description': 'Devices only',
            'link_name': '^$',
            'link_name_regex': 'y'
        },
        {
            'name': 'Links only',
            'description': 'Links only',
            'device_name': '^$',
            'device_name_regex': 'y'
        }
    ):
        factory('Pool', **pool)


@integrity_rollback
def create_default_parameters():
    parameters = classes['Parameters']()
    db.session.add(parameters)
    db.session.commit()


@integrity_rollback
def create_default_network_topology(app):
    with open(join(app.path, 'projects', 'usa.xls'), 'rb') as f:
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
                factory(cls, **kwargs)
            db.session.commit()


@integrity_rollback
def create_default_services():
    for service in (
        {
            'type': 'swiss_army_knife_service',
            'name': 'Start',
            'description': 'Start point of a workflow',
            'hidden': True
        },
        {
            'type': 'swiss_army_knife_service',
            'name': 'End',
            'description': 'End point of a workflow',
            'hidden': True
        },
        {
            'type': 'swiss_army_knife_service',
            'name': 'mail_feedback_notification',
            'description': 'Mail notification (service logs)'
        },
        {
            'type': 'swiss_army_knife_service',
            'name': 'slack_feedback_notification',
            'description': 'Slack notification (service logs)'
        },
        {
            'type': 'swiss_army_knife_service',
            'name': 'mattermost_feedback_notification',
            'description': 'Mattermost notification (service logs)'
        }
    ):
        factory(service.pop('type'), **service)


@integrity_rollback
def create_example_services():
    for service in (
        {
            'type': 'configure_bgp_service',
            'name': 'napalm_configure_bgp_1',
            'description': 'Configure BGP Peering with Napalm',
            'devices': [fetch('Device', name='Washington')],
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
            'type': 'netmiko_configuration_service',
            'name': 'netmiko_create_vrf_test',
            'description': 'Create a VRF "test" with Netmiko',
            'waiting_time': 0,
            'devices': [fetch('Device', name='Washington')],
            'vendor': 'Arista',
            'operating_system': 'eos',
            'driver': 'arista_eos',
            'global_delay_factor': '1.0',
            'content': 'vrf definition test',
            'enable_mode': 'y',
            'fast_cli': 'y',
            'timeout': 3
        },
        {
            'type': 'netmiko_validation_service',
            'name': 'netmiko_check_vrf_test',
            'description': 'Check that the vrf "test" is configured',
            'waiting_time': 0,
            'devices': [fetch('Device', name='Washington')],
            'vendor': 'Arista',
            'operating_system': 'eos',
            'driver': 'arista_eos',
            'command': 'show vrf',
            'content_match': 'test',
            'fast_cli': 'y',
            'timeout': 3
        },
        {
            'type': 'netmiko_configuration_service',
            'name': 'netmiko_delete_vrf_test',
            'description': 'Delete VRF "test"',
            'waiting_time': 1,
            'devices': [fetch('Device', name='Washington')],
            'vendor': 'Arista',
            'operating_system': 'eos',
            'driver': 'arista_eos',
            'global_delay_factor': '1.0',
            'content': 'no vrf definition test',
            'enable_mode': 'y',
            'fast_cli': 'y',
            'timeout': 3
        },
        {
            'type': 'netmiko_validation_service',
            'name': 'netmiko_check_no_vrf_test',
            'description': 'Check that the vrf "test" is NOT configured',
            'waiting_time': 0,
            'devices': [fetch('Device', name='Washington')],
            'vendor': 'Arista',
            'operating_system': 'eos',
            'driver': 'arista_eos',
            'command': 'show vrf',
            'content_match': '^((?!test).)*$',
            'content_match_regex': 'y',
            'fast_cli': 'y',
            'timeout': 3,
            'number_of_retries': 2,
            'time_between_retries': 1
        },
    ):
        instance = factory(service.pop('type'), **service)
        services.append(instance)
    workflow = factory('Workflow', **{
        'name': 'Netmiko_VRF_workflow',
        'description': 'Create and delete a VRF with Netmiko',
        'vendor': 'Arista',
        'operating_system': 'eos'
    })
    workflow.jobs.extend(services)
    edges = [(0, 2), (2, 3), (3, 4), (4, 5), (5, 1)]
    for x, y in edges:
        factory('WorkflowEdge', **{
            'name': f'{workflow.name} {x} -> {y}',
            'workflow': workflow,
            'type': True,
            'source': workflow.jobs[x],
            'destination': workflow.jobs[y]
        })
    positions = [(-20, 0), (20, 0), (0, -15), (0, -5), (0, 5), (0, 15)]
    for index, (x, y) in enumerate(positions):
        workflow.jobs[index].positions['Netmiko_VRF_workflow'] = x * 10, y * 10


@integrity_rollback
def create_napalm_workflow():
    services = []
    for service in (
        {
            'type': 'napalm_configuration_service',
            'name': 'napalm_create_vrf_test',
            'description': 'Create a VRF "test" with Napalm',
            'waiting_time': 0,
            'devices': [fetch('Device', name='Washington')],
            'driver': 'eos',
            'vendor': 'Arista',
            'operating_system': 'eos',
            'content_type': 'simple',
            'action': 'load_merge_candidate',
            'content': 'vrf definition test\n'
        },
        {
            'type': 'napalm_rollback_service',
            'name': 'Napalm eos Rollback',
            'driver': 'eos',
            'description': 'Rollback a configuration with Napalm eos',
            'devices': [fetch('Device', name='Washington')],
            'waiting_time': 0
        }
    ):
        instance = factory(service.pop('type'), **service)
        services.append(instance)
    services.insert(1, fetch('Job', name='netmiko_check_vrf_test'))
    services.append(fetch('Job', name=f'netmiko_check_no_vrf_test'))
    workflow = factory('Workflow', **{
        'name': 'Napalm_VRF_workflow',
        'description': 'Create and delete a VRF with Napalm',
        'vendor': 'Arista',
        'operating_system': 'eos'
    })
    workflow.jobs.extend(services)
    edges = [(0, 2), (2, 3), (3, 4), (4, 5), (5, 1)]
    for x, y in edges:
        factory('WorkflowEdge', **{
            'name': f'{workflow.name} {x} -> {y}',
            'workflow': workflow,
            'type': True,
            'source': workflow.jobs[x],
            'destination': workflow.jobs[y]
        })
    positions = [(-20, 0), (20, 0), (0, -15), (0, -5), (0, 5), (0, 15)]
    for index, (x, y) in enumerate(positions):
        workflow.jobs[index].positions['Napalm_VRF_workflow'] = x * 10, y * 10


def create_payload_transfer_workflow():
    services = []
    for service in [{
        'name': 'GET_device',
        'type': 'rest_call_service',
        'description': 'Use GET ReST call on eNMS ReST API',
        'username': 'admin',
        'password': 'admin',
        'waiting_time': 0,
        'devices': [fetch('Device', name='Washington')],
        'content_match': '',
        'call_type': 'GET',
        'url': 'http://127.0.0.1:5000/rest/object/device/{{device.name}}',
        'payload': '',
        'multiprocessing': 'y'
    }] + [{
        'name': f'{getter}',
        'type': 'napalm_getters_service',
        'description': f'Getter: {getter}',
        'waiting_time': 0,
        'devices': [fetch('Device', name='Washington')],
        'driver': 'eos',
        'content_match': '',
        'getters': [getter]
    } for getter in (
        'get_facts',
        'get_interfaces',
        'get_interfaces_ip',
        'get_config'
    )] + [{
        'name': 'process_payload1',
        'type': 'swiss_army_knife_service',
        'description': 'Process Payload in example workflow',
        'waiting_time': 0,
        'devices': [fetch('Device', name='Washington')]
    }]:
        instance = factory(service.pop('type'), **service)
        services.append(instance)
    workflow = factory('Workflow', **{
        'name': 'payload_transfer_workflow',
        'description': 'ReST call, Napalm getters, etc',
        'vendor': 'Arista',
        'operating_system': 'eos'
    })
    workflow.jobs.extend(services)

    # create workflow edges with following schema:
    positions = [
        (-20, 0),
        (50, 0),
        (-5, 0),
        (-5, -10),
        (15, 10),
        (15, -10),
        (30, -10),
        (30, 0)
    ]
    for index, (x, y) in enumerate(positions):
        job = workflow.jobs[index]
        job.positions['payload_transfer_workflow'] = x * 10, y * 10
    edges = [(0, 2), (2, 3), (2, 4), (3, 5), (5, 6), (6, 7), (4, 7), (7, 1)]
    for x, y in edges:
        factory('WorkflowEdge', **{
            'name': f'{workflow.name} {x} -> {y}',
            'workflow': workflow,
            'type': True,
            'source': workflow.jobs[x],
            'destination': workflow.jobs[y]
        })


def create_default_examples(app):
    create_default_network_topology(app),
    create_example_services()
    create_netmiko_workflow()
    create_napalm_workflow()
    create_payload_transfer_workflow()

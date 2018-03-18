from tasks.models import (
    NapalmGettersTask,
    Task
)
from test_base import check_blueprints
from test_objects import create_from_file
from werkzeug.datastructures import ImmutableMultiDict

## NAPALM getters task

getters_once_dict = ImmutableMultiDict([
    ('name', 'getters_once'),
    ('getters', 'get_arp_table'),
    ('getters', 'get_interfaces_counters'),
    ('getters', 'get_interfaces'),
    ('getters', 'get_lldp_neighbors'),
    ('scheduled_date', ''),
    ('frequency', ''),
    ('script_type', 'napalm_getters')
])

getters_recurrent = ImmutableMultiDict([
    ('name', 'getters_recurrent'),
    ('getters', 'get_network_instances'),
    ('getters', 'get_ntp_peers'),
    ('getters', 'get_bgp_config'),
    ('getters', 'get_bgp_neighbors'),
    ('scheduled_date', '15/03/2020 20:47:15'),
    ('frequency', '160'),
    ('script_type', 'napalm_getters')
])


@check_blueprints('/views', '/tasks')
def test_napalm_getters_task(user_client):
    create_from_file(user_client, 'europe.xls')
    with user_client.session_transaction() as sess:
        sess['selection'] = ['1', '21', '22']
    user_client.post('views/geographical_view', data=getters_once_dict)
    assert len(NapalmGettersTask.query.all()) == 1
    with user_client.session_transaction() as sess:
        sess['selection'] = ['13', '15', '17']
    user_client.post('views/geographical_view', data=getters_recurrent)
    assert len(NapalmGettersTask.query.all()) == 2
    assert len(Task.query.all()) == 2
    for task in ('getters_once', 'getters_recurrent'):
        getter_task = ImmutableMultiDict([('task_name', task)])
        user_client.post('tasks/delete_task', data=getter_task)


## NAPALM and Netmiko configuration task

simple_script = ImmutableMultiDict([
    ('name', 'ping'),
    ('type', 'simple'),
    ('create_script', ''),
    ('text', 'ping 1.1.1.1')
])

netmiko_task = ImmutableMultiDict([
    ('name', 'ping_task_once'),
    ('script', 'ping'),
    ('type', 'show_commands'),
    ('driver', 'cisco_ios_ssh'),
    ('global_delay_factor', '1.0'),
    ('start_date', ''),
    ('end_date', ''),
    ('frequency', ''),
    ('script_type', 'netmiko_configuration')
])


@check_blueprints('/views', '/tasks')
def test_configuration_tasks(user_client):
    create_from_file(user_client, 'europe.xls')
    user_client.post('/scripts/configuration_script', data=simple_script)
    with user_client.session_transaction() as sess:
        sess['selection'] = ['1', '21', '22']
    user_client.post('views/geographical_view', data=netmiko_task)

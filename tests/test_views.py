from conftest import path_scripts
from os.path import join
from tasks.models import (
    NapalmConfigTask,
    NapalmGettersTask,
    NetmikoConfigTask,
    Task
)
from test_base import check_blueprints
from test_objects import create_from_file
from test_scripts import simple_script, jinja2_script
from werkzeug.datastructures import ImmutableMultiDict

## NAPALM getters task

getters_dict1 = ImmutableMultiDict([
    ('name', 'getters_dict1'),
    ('getters', 'get_arp_table'),
    ('getters', 'get_interfaces_counters'),
    ('getters', 'get_interfaces'),
    ('getters', 'get_lldp_neighbors'),
    ('start_date', '15/03/2030 20:47:15'),
    ('end_date', '15/03/2099 20:47:15'),
    ('frequency', '160'),
    ('script_type', 'napalm_getters')
])

getters_dict2 = ImmutableMultiDict([
    ('name', 'getters_dict2'),
    ('getters', 'get_network_instances'),
    ('getters', 'get_ntp_peers'),
    ('getters', 'get_bgp_config'),
    ('getters', 'get_bgp_neighbors'),
    ('start_date', '15/03/2030 20:47:15'),
    ('end_date', '15/03/2099 20:47:15'),
    ('frequency', '160'),
    ('script_type', 'napalm_getters')
])


@check_blueprints('/views', '/tasks')
def test_napalm_getters_task(user_client):
    create_from_file(user_client, 'europe.xls')
    with user_client.session_transaction() as sess:
        sess['selection'] = ['1', '21', '22']
    user_client.post('views/geographical_view', data=getters_dict1)
    assert len(NapalmGettersTask.query.all()) == 1
    with user_client.session_transaction() as sess:
        sess['selection'] = ['13', '15', '17']
    user_client.post('views/geographical_view', data=getters_dict2)
    assert len(NapalmGettersTask.query.all()) == 2
    assert len(Task.query.all()) == 2
    for task in ('getters_dict1', 'getters_dict2'):
        getter_task = ImmutableMultiDict([('task_name', task)])
        user_client.post('tasks/delete_task', data=getter_task)


## NAPALM and Netmiko show and configuration task

netmiko_show = ImmutableMultiDict([
    ('name', 'ping_task_once'),
    ('script', 'ping'),
    ('type', 'show_commands'),
    ('driver', 'cisco_ios_ssh'),
    ('global_delay_factor', '1.0'),
    ('frequency', '160'),
    ('start_date', '15/03/2030 20:47:15'),
    ('end_date', '15/03/2099 20:47:15'),
    ('script_type', 'netmiko_configuration')
])


@check_blueprints('/views', '/tasks')
def test_netmiko_show(user_client):
    create_from_file(user_client, 'europe.xls')
    user_client.post('/scripts/configuration_script', data=simple_script)
    with user_client.session_transaction() as sess:
        sess['selection'] = ['1', '21', '22']
    user_client.post('views/geographical_view', data=netmiko_show)


netmiko_config = ImmutableMultiDict([
    ('name', 'test_netmiko_config'),
    ('script', 'subif'),
    ('start_date', '01/06/2090 18:59:11'),
    ('end_date', '01/06/2099 18:59:11'),
    ('frequency', '10000'),
    ('script_type', 'netmiko_configuration')
])

napalm_config = ImmutableMultiDict([
    ('name', 'test'),
    ('script', 'subif'),
    ('start_date', '01/06/2090 18:59:11'),
    ('end_date', '01/06/2099 18:59:11'),
    ('frequency', '10000'),
])


@check_blueprints('/views', '/tasks')
def test_netmiko_napalm_config(user_client):
    create_from_file(user_client, 'europe.xls')
    path_yaml = join(path_scripts, 'cisco', 'interfaces', 'parameters.yaml')
    with open(path_yaml, 'rb') as f:
        jinja2_script['file'] = f
        user_client.post('/scripts/configuration_script', data=jinja2_script)
    with user_client.session_transaction() as sess:
        sess['selection'] = ['1', '21', '22']
    user_client.post('views/geographical_view', data=netmiko_config)
    user_client.post('views/geographical_view', data=napalm_config)
    assert len(NapalmConfigTask.query.all()) == 1
    assert len(NetmikoConfigTask.query.all()) == 1
    assert len(Task.query.all()) == 2


## Google Earth export

google_earth_dict = ImmutableMultiDict([
    ('name', 'test_google_earth'),
    ('label_size', '1'),
    ('line_width', '2'),
    ('netmiko_script', '')
])


@check_blueprints('/views')
def test_google_earth(user_client):
    create_from_file(user_client, 'europe.xls')
    user_client.post('/views/google_earth_export', data=google_earth_dict)

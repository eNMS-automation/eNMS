from conftest import path_scripts
from os.path import join
from tasks.models import Task
from test_base import check_blueprints
from test_objects import create_from_file
from test_scripts import netmiko_ping, napalm_jinja2_script
from werkzeug.datastructures import ImmutableMultiDict


instant_task = ImmutableMultiDict([
    ('name', 'instant_task'),
    ('scripts', 'napalm_subif'),
    ('scripts', 'netmiko_ping'),
    ('start_date', ''),
    ('end_date', ''),
    ('frequency', ''),
    ('script', '')
])

scheduled_task = ImmutableMultiDict([
    ('name', 'scheduled_task'),
    ('scripts', 'napalm_subif'),
    ('scripts', 'netmiko_ping'),
    ('start_date', '30/03/2018 19:10:13'),
    ('end_date', '06/04/2018 19:10:13'),
    ('frequency', '3600'),
    ('script', '')
])


@check_blueprints('/views', '/tasks')
def test_netmiko_napalm_config(user_client):
    create_from_file(user_client, 'europe.xls')
    user_client.post('/scripts/create_script_netmiko_config', data=netmiko_ping)
    path_yaml = join(path_scripts, 'interfaces', 'parameters.yaml')
    with open(path_yaml, 'rb') as f:
        napalm_jinja2_script['file'] = f
        user_client.post('/scripts/create_script_napalm_config', data=napalm_jinja2_script)
    with user_client.session_transaction() as sess:
        sess['selection'] = ['1', '21', '22']
    user_client.post('tasks/scheduler', data=instant_task)
    user_client.post('tasks/scheduler', data=scheduled_task)
    assert len(Task.query.all()) == 2


## Google Earth export

google_earth_dict = ImmutableMultiDict([
    ('google earth', ''),
    ('name', 'test_google_earth'),
    ('label_size', '1'),
    ('line_width', '2'),
    ('netmiko_script', '')
])


# @check_blueprints('/views')
# def test_google_earth(user_client):
#     create_from_file(user_client, 'europe.xls')
#     user_client.post('/views/export_to_google_earth', data=google_earth_dict)

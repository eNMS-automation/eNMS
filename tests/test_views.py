# from os.path import join
from werkzeug.datastructures import ImmutableMultiDict

# from eNMS.base.helpers import get_obj
# from eNMS.objects.models import Node
# from eNMS.scripts.models import Script
# from eNMS.tasks.models import Task

from tests.test_base import check_blueprints
from tests.test_objects import create_from_file
# from tests.test_scripts import netmiko_ping, napalm_jinja2_script


instant_task = ImmutableMultiDict([
    ('name', 'instant_task'),
    ('nodes', '8'),
    ('nodes', '9'),
    ('start_date', ''),
    ('end_date', ''),
    ('frequency', ''),
    ('scripts', '1')
])

scheduled_task = ImmutableMultiDict([
    ('name', 'scheduled_task'),
    ('nodes', 'router8'),
    ('nodes', 'router9'),
    ('start_date', '30/03/2018 19:10:13'),
    ('end_date', '06/04/2018 19:10:13'),
    ('frequency', '3600'),
    ('scripts', '1')
])


# @check_blueprints('/views', '/tasks')
# def test_netmiko_napalm_config(user_client):
#     create_from_file(user_client, 'europe.xls')
#     user_client.post('/scripts/create_script_netmiko_config', data=netmiko_ping)
#     path_yaml = join(user_client.application.path, 'scripts', 'interfaces', 'parameters.yaml')
#     with open(path_yaml, 'rb') as f:
#         napalm_jinja2_script['file'] = f
#         user_client.post('/scripts/create_script_napalm_config', data=napalm_jinja2_script)
#     assert len(Script.query.all()) == 7
#     user_client.post('tasks/scheduler/script_task', data=instant_task)
#     user_client.post('tasks/scheduler/script_task', data=scheduled_task)
#     assert len(Task.query.all()) == 2


## Google Earth export

google_earth_dict = ImmutableMultiDict([
    ('google earth', ''),
    ('name', 'test_google_earth'),
    ('label_size', '1'),
    ('line_width', '2'),
    ('netmiko_script', '')
])


@check_blueprints('/views')
def test_google_earth(user_client):
    create_from_file(user_client, 'europe.xls')
    user_client.post('/views/export_to_google_earth', data=google_earth_dict)

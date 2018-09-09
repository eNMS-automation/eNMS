from werkzeug.datastructures import ImmutableMultiDict

from eNMS.tasks.models import Task

from tests.test_base import check_blueprints
from tests.test_objects import create_from_file


instant_task = ImmutableMultiDict([
    ('name', 'instant_task'),
    ('waiting_time', '0'),
    ('devices', '1'),
    ('devices', '2'),
    ('start_date', ''),
    ('end_date', ''),
    ('frequency', ''),
    ('job', '2'),
    ('run_immediately', 'y')
])

scheduled_task = ImmutableMultiDict([
    ('name', 'scheduled_task'),
    ('waiting_time', '0'),
    ('devices', '1'),
    ('devices', '2'),
    ('start_date', '30/03/2018 19:10:13'),
    ('end_date', '06/04/2018 19:10:13'),
    ('frequency', '3600'),
    ('job', '2'),
    ('run_immediately', 'y')
])


@check_blueprints('/views', '/tasks')
def test_netmiko_napalm_config(user_client):
    create_from_file(user_client, 'europe.xls')
    user_client.post('tasks/scheduler', data=instant_task)
    assert len(Task.query.all()) == 12
    user_client.post('tasks/scheduler', data=scheduled_task)
    assert len(Task.query.all()) == 13


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
#     user_client.post(
#         '/views/export_to_google_earth',
#         data=google_earth_dict
#     )

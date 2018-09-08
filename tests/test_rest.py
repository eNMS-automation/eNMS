from json import dumps, loads
from requests import delete, get, post, put
from time import sleep
from werkzeug.datastructures import ImmutableMultiDict

from eNMS.objects.models import Device
from eNMS.scripts.models import Script
from eNMS.tasks.models import Task

device = {
    "name": "router10",
    "description": "france",
    "model": "None",
    "location": "france",
    "type": "Router",
    "vendor": "Cisco",
    "operating_system": "IOS",
    "os_version": "15.5(3)M",
    "ip_address": "192.168.1.187",
    "longitude": "4.533886327086546",
    "latitude": "46.386212676269515"
}

expected_response = {
    "id": "1",
    "name": "router10",
    "description": "france",
    "model": "None",
    "location": "france",
    "type": "Router",
    "vendor": "Cisco",
    "operating_system": "IOS",
    "os_version": "15.5(3)M",
    "ip_address": "192.168.1.187",
    "longitude": "4.533886327086546",
    "latitude": "46.386212676269515",
    "tasks": [],
    "pools": []
}

updated_device = {
    "name": "router10",
    "description": "france",
    "model": "None",
    "location": "france",
    "type": "Router",
    "vendor": "Juniper",
    "operating_system": "IOS",
    "os_version": "15.5(3)M",
    "ip_address": "192.168.1.187",
    "longitude": "4.533886327086546",
    "latitude": "46.386212676269515"
}

updated_response = {
    "id": "1",
    "name": "router10",
    "description": "france",
    "model": "None",
    "location": "france",
    "type": "Router",
    "vendor": "Juniper",
    "operating_system": "IOS",
    "os_version": "15.5(3)M",
    "ip_address": "192.168.1.187",
    "longitude": "4.533886327086546",
    "latitude": "46.386212676269515",
    "tasks": [],
    "pools": []
}


def rest_api_test(user_client):
    # POST: object creation
    response = post(
        'http://127.0.0.1:5000/rest/object/device',
        data=dumps(device)
    )
    assert loads(response.content) == expected_response
    assert len(Device.query.all()) == 1
    # GET: retrieve object properties
    response = get(
        'http://127.0.0.1:5000/rest/object/device/router10',
        headers={'Accept': 'application/json'}
    )
    assert loads(response.content) == expected_response
    assert len(Device.query.all()) == 1
    # PUT: update object properties
    put('http://127.0.0.1:5000/rest/object/device', data=dumps(updated_device))
    response = get(
        'http://127.0.0.1:5000/rest/object/device/router10',
        headers={'Accept': 'application/json'}
    )
    assert loads(response.content) == updated_response
    assert len(Device.query.all()) == 1
    # DELETE: delete an object
    delete(
        'http://127.0.0.1:5000/rest/object/device/router10',
        headers={'Accept': 'application/json'}
    )
    assert len(Device.query.all()) == 0


post_script = ImmutableMultiDict([
    ('name', 'create_router10'),
    ('description', 'POST creation'),
    ('call_type', 'POST'),
    ('url', 'http://127.0.0.1:5000/rest/object/device'),
    ('payload', dumps(device)),
    ('username', ''),
    ('password', ''),
    ('content', '.*15.5(\\d)M.*'),
    ('content_regex', 'y')
])

post_script_task = ImmutableMultiDict([
    ('name', 'task_create_router'),
    ('waiting_time', '0'),
    ('job', '4'),
    ('start_date', ''),
    ('end_date', ''),
    ('frequency', ''),
    ('run_immediately', 'y')
])

delete_script = ImmutableMultiDict([
    ('name', 'delete_router10'),
    ('description', 'DELETE'),
    ('call_type', 'DELETE'),
    ('url', 'http://127.0.0.1:5000/rest/object/device/router10'),
    ('payload', ''),
    ('username', ''),
    ('password', ''),
    ('content', '.*15.5(\\d)M.*'),
    ('content_regex', 'y')
])

delete_script_task = ImmutableMultiDict([
    ('name', 'task_delete_router'),
    ('waiting_time', '0'),
    ('job', '5'),
    ('start_date', '30/03/2038 19:10:13'),
    ('end_date', ''),
    ('frequency', ''),
    ('run_immediately', 'y')
])


def rest_script_test(user_client):
    user_client.post('/scripts/create_script/rest_call', data=post_script)
    assert len(Script.query.all()) == 4
    user_client.post('/tasks/scheduler', data=post_script_task)
    get(
        'http://127.0.0.1:5000/rest/execute_task/task_create_router',
        headers={'Accept': 'application/json'}
    )
    assert len(Task.query.all()) == 1
    # wait a bit for the task to run
    sleep(30)
    assert len(Device.query.all()) == 1
    user_client.post('/scripts/create_script/rest_call', data=delete_script)
    assert len(Script.query.all()) == 5
    user_client.post('/tasks/scheduler', data=delete_script_task)
    assert len(Task.query.all()) == 2
    get(
        'http://127.0.0.1:5000/rest/execute_task/task_delete_router',
        headers={'Accept': 'application/json'}
    )
    # wait a bit for the task to run
    sleep(30)
    assert len(Device.query.all()) == 0

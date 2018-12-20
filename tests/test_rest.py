from json import dumps, loads
from requests import delete, get, post, put
from time import sleep
from werkzeug.datastructures import ImmutableMultiDict

from eNMS.base.helpers import fetch_all

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


def test_rest_api(user_client):
    response = post(
        'http://192.168.105.2:5000/rest/object/device',
        data=dumps(device)
    )
    assert loads(response.content) == expected_response
    assert len(fetch_all('Device')) == 1
    response = get(
        'http://192.168.105.2:5000/rest/object/device/router10',
        headers={'Accept': 'application/json'}
    )
    assert loads(response.content) == expected_response
    assert len(fetch_all('Device')) == 1
    put('http://192.168.105.2:5000/rest/object/device', data=dumps(updated_device))
    response = get(
        'http://192.168.105.2:5000/rest/object/device/router10',
        headers={'Accept': 'application/json'}
    )
    assert loads(response.content) == updated_response
    assert len(fetch_all('Device')) == 1
    delete(
        'http://192.168.105.2:5000/rest/object/device/router10',
        headers={'Accept': 'application/json'}
    )
    assert len(fetch_all('Device')) == 0

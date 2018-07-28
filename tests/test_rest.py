from json import dumps, loads
from requests import delete, get, post, put

from eNMS.objects.models import Node

node = {
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
    "scheduled_tasks": [],
    "inner_tasks": [],
    "pools": []
}

updated_node = {
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
    "scheduled_tasks": [],
    "inner_tasks": [],
    "pools": []
}


def test_rest_api(user_client):
    # POST: object creation
    response = post('http://127.0.0.1:5000/rest/object/node', data=dumps(node))
    assert loads(response.content) == expected_response
    assert len(Node.query.all()) == 1
    # GET: retrieve object properties
    response = get(
        'http://127.0.0.1:5000/rest/object/node/router10',
        headers={'Accept': 'application/json'}
    )
    assert loads(response.content) == expected_response
    assert len(Node.query.all()) == 1
    # PUT: update object properties
    put('http://127.0.0.1:5000/rest/object/node', data=dumps(updated_node))
    response = get(
        'http://127.0.0.1:5000/rest/object/node/router10',
        headers={'Accept': 'application/json'}
    )
    assert loads(response.content) == updated_response
    assert len(Node.query.all()) == 1
    delete(
        'http://127.0.0.1:5000/rest/object/node/router10',
        headers={'Accept': 'application/json'}
    )
    assert len(Node.query.all()) == 0

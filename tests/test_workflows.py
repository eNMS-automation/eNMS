from requests import post
from requests.auth import HTTPBasicAuth

from tests.test_base import check_blueprints


@check_blueprints('/automation')
def test_payload_transfer_workflow(user_client):
    result = post(
        'http://192.168.105.2:5000/rest/run_job',
        json={'name': 'payload_transfer_workflow', 'async': 0},
        auth=HTTPBasicAuth('admin', 'admin')
    ).json()
    assert result['success'] and len(result) == 10


@check_blueprints('/automation')
def test_netmiko_workflow(user_client):
    result = post(
        'http://192.168.105.2:5000/rest/run_job',
        json={'name': 'Netmiko_VRF_workflow', 'async': 0},
        auth=HTTPBasicAuth('admin', 'admin')
    ).json()
    assert result['success'] and len(result) == 8


@check_blueprints('/automation')
def test_napalm_workflow(user_client):
    result = post(
        'http://192.168.105.2:5000/rest/run_job',
        json={'name': 'Napalm_VRF_workflow', 'async': 0},
        auth=HTTPBasicAuth('admin', 'admin')
    ).json()
    assert not result['success'] and len(result) == 7

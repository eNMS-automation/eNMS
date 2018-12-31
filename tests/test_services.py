from tests.test_base import check_blueprints
from werkzeug.datastructures import ImmutableMultiDict

from eNMS.base.helpers import fetch_all


netmiko_ping = ImmutableMultiDict([
    ('name', 'netmiko_ping'),
    ('waiting_time', '0'),
    ('devices', '1'),
    ('devices', '2'),
    ('description', ''),
    ('vendor', ''),
    ('operating_system', ''),
    ('content_type', 'simple'),
    ('content', 'ping 1.1.1.1'),
    ('netmiko_type', 'show_commands'),
    ('driver', 'cisco_xr_ssh'),
    ('global_delay_factor', '1.0')
])

file_transfer_service = ImmutableMultiDict([
    ('name', 'test'),
    ('waiting_time', '0'),
    ('devices', '1'),
    ('devices', '2'),
    ('description', ''),
    ('vendor', ''),
    ('operating_system', ''),
    ('driver', 'cisco_ios'),
    ('source_file', 'path/to/source'),
    ('dest_file', 'path/to/destination'),
    ('file_system', 'flash:'),
    ('direction', 'put')
])


@check_blueprints('/automation')
def test_base_services(user_client):
    user_client.post(
        '/update/NetmikoConfigurationService',
        data=netmiko_ping
    )
    assert len(fetch_all('NetmikoConfigurationService')) == 3
    assert len(fetch_all('Service')) == 24
    user_client.post(
        '/update/NetmikoFileTransferService',
        data=file_transfer_service
    )
    assert len(fetch_all('NetmikoFileTransferService')) == 1
    assert len(fetch_all('Service')) == 25


getters_dict = ImmutableMultiDict([
    ('name', 'napalm_getters_service'),
    ('description', ''),
    ('driver', 'ios'),
    ('list_fields', 'getters'),
    ('getters', 'get_interfaces'),
    ('getters', 'get_interfaces_ip'),
    ('getters', 'get_lldp_neighbors')
])


@check_blueprints('/automation')
def test_getters_service(user_client):
    user_client.post(
        '/update/NapalmGettersService',
        data=getters_dict
    )
    assert len(fetch_all('NapalmGettersService')) == 5


ansible_service = ImmutableMultiDict([
    ('name', 'testttt'),
    ('waiting_time', '0'),
    ('devices', '1'),
    ('devices', '2'),
    ('description', ''),
    ('vendor', ''),
    ('operating_system', ''),
    ('playbook_path', 'test.yml'),
    ('arguments', '--ask-vault')
])


@check_blueprints('/automation')
def test_ansible_services(user_client):
    user_client.post(
        '/update/AnsiblePlaybookService',
        data=ansible_service
    )
    assert len(fetch_all('AnsiblePlaybookService')) == 1
    assert len(fetch_all('Service')) == 24

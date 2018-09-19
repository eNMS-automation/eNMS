from eNMS import db
from os.path import join
from eNMS.services.models import (
    AnsibleService,
    NapalmConfigService,
    NapalmGettersService,
    NetmikoConfigService,
    FileTransferService,
    Service
)
from tests.test_base import check_blueprints
from werkzeug.datastructures import ImmutableMultiDict

# test the creation of configuration service (netmiko / napalm)
# test the creation of file transfer service (netmiko via SCP)
# test the creation of ansible service


netmiko_ping = ImmutableMultiDict([
    ('name', 'netmiko_ping'),
    ('waiting_time', '0'),
    ('description', ''),
    ('vendor', ''),
    ('operating_system', ''),
    ('content_type', 'simple'),
    ('create_service', 'netmiko_config'),
    ('content', 'ping 1.1.1.1'),
    ('netmiko_type', 'show_commands'),
    ('driver', 'cisco_xr_ssh'),
    ('global_delay_factor', '1.0'),
])

file_transfer_service = ImmutableMultiDict([
    ('name', 'test'),
    ('waiting_time', '0'),
    ('description', ''),
    ('vendor', ''),
    ('operating_system', ''),
    ('driver', 'cisco_ios'),
    ('source_file', 'path/to/source'),
    ('dest_file', 'path/to/destination'),
    ('file_system', 'flash:'),
    ('direction', 'put'),
    ('create_service', 'file_transfer'),
])


@check_blueprints('/services')
def test_base_services(user_client):
    user_client.post(
        '/services/create_service/netmiko_config',
        data=netmiko_ping
    )
    assert len(NetmikoConfigService.query.all()) == 3
    path_yaml = join(
        user_client.application.path,
        'scripts',
        'interfaces',
        'parameters.yaml'
    )
    assert len(Service.query.all()) == 8
    user_client.post(
        'services/create_service/file_transfer',
        data=file_transfer_service
    )
    assert len(FileTransferService.query.all()) == 1
    assert len(Service.query.all()) == 11


getters_dict = ImmutableMultiDict([
    ('name', 'napalm_getters_service'),
    ('waiting_time', '0'),
    ('description', ''),
    ('getters', 'get_interfaces'),
    ('getters', 'get_interfaces_ip'),
    ('getters', 'get_lldp_neighbors'),
    ('create_service', 'napalm_getters')
])


@check_blueprints('/services')
def test_getters_service(user_client):
    user_client.post(
        '/services/create_service/napalm_getters',
        data=getters_dict
    )
    assert len(NapalmGettersService.query.all()) == 2


ansible_service = ImmutableMultiDict([
    ('name', 'testttt'),
    ('waiting_time', '0'),
    ('description', ''),
    ('vendor', ''),
    ('operating_system', ''),
    ('playbook_path', 'test.yml'),
    ('arguments', '--ask-vault')
])


@check_blueprints('/services')
def test_ansible_services(user_client):
    user_client.post(
        '/services/create_service/ansible_playbook',
        data=ansible_service
    )
    assert len(AnsibleService.query.all()) == 1
    assert len(Service.query.all()) == 8

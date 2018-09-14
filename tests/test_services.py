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

template = '''
{% for interface, properties in subinterfaces.items() %}
interface FastEthernet0/0.{{ interface }}
description {{ properties.aire }}
encapsulation dot1Q {{ properties.dot1Q }}
ip address {{ properties.address }} 255.255.255.248
no ip redirects
ip ospf cost {{ properties.cost }}
{% endfor %}
'''

result = '''
interface FastEthernet0/0.420
description 262
encapsulation dot1Q 420
ip address 10.124.33.250 255.255.255.248
no ip redirects
ip ospf cost 320

interface FastEthernet0/0.418
description 252
encapsulation dot1Q 418
ip address 10.124.33.234 255.255.255.248
no ip redirects
ip ospf cost 520

interface FastEthernet0/0.419
description 261
encapsulation dot1Q 419
ip address 10.124.33.242 255.255.255.248
no ip redirects
ip ospf cost 620
'''

netmiko_jinja2_service = dict([
    ('name', 'netmiko_subif'),
    ('waiting_time', '0'),
    ('description', ''),
    ('vendor', ''),
    ('operating_system', ''),
    ('content_type', 'j2_template'),
    ('create_service', 'netmiko_config'),
    ('content', template),
    ('netmiko_type', 'configuration'),
    ('driver', 'cisco_xr_ssh'),
    ('global_delay_factor', '1.0'),
])

napalm_jinja2_service = dict([
    ('name', 'napalm_subif'),
    ('waiting_time', '0'),
    ('description', ''),
    ('vendor', ''),
    ('operating_system', ''),
    ('content_type', 'j2_template'),
    ('create_service', 'napalm_config'),
    ('content', template),
    ('service_type', 'napalm_configuration'),
    ('action', 'load_merge_candidate')
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
    with open(path_yaml, 'rb') as f:
        netmiko_jinja2_service['file'] = f
        user_client.post(
            '/services/create_service/netmiko_config',
            data=netmiko_jinja2_service
        )
    with open(path_yaml, 'rb') as f:
        napalm_jinja2_service['file'] = f
        user_client.post(
            '/services/create_service/napalm_config',
            data=napalm_jinja2_service
        )
    assert len(NapalmConfigService.query.all()) == 2
    assert len(Service.query.all()) == 10
    netmiko_j2_service = db.session.query(Service).filter_by(
        name='netmiko_subif'
    ).first()
    napalm_j2_service = db.session.query(Service).filter_by(
        name='napalm_subif'
    ).first()
    # simply removing the space does not work as yaml relies on dict, which are
    # not ordered, we use set instead for the test to pass on python 2 and 3
    assert set(netmiko_j2_service.content.split('\n')) == set(result.split('\n'))
    assert set(napalm_j2_service.content.split('\n')) == set(result.split('\n'))
    # file transfer service
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

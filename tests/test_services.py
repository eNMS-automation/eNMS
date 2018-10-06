from eNMS.services.models import Service, service_classes
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
    ('content', 'ping 1.1.1.1'),
    ('netmiko_type', 'show_commands'),
    ('driver', 'cisco_xr_ssh'),
    ('global_delay_factor', '1.0')
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
    ('direction', 'put')
])


@check_blueprints('/services')
def test_base_services(user_client):
    user_client.post(
        '/services/save_service/Netmiko Configuration Service',
        data=netmiko_ping
    )
    assert len(
        service_classes['Netmiko Configuration Service'].query.all()
    ) == 3
    assert len(Service.query.all()) == 14
    user_client.post(
        'services/save_service/Netmiko File Transfer Service',
        data=file_transfer_service
    )
    assert len(
        service_classes['Netmiko File Transfer Service'].query.all()
    ) == 1
    assert len(Service.query.all()) == 15


getters_dict = ImmutableMultiDict([
    ('name', 'napalm_getters_service'),
    ('description', ''),
    ('driver', 'ios'),
    ('getters', 'get_interfaces'),
    ('getters', 'get_interfaces_ip'),
    ('getters', 'get_lldp_neighbors')
])


@check_blueprints('/services')
def test_getters_service(user_client):
    user_client.post(
        '/services/save_service/Napalm Getters Service',
        data=getters_dict
    )
    assert len(service_classes['Napalm Getters Service'].query.all()) == 5


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
        '/services/save_service/Ansible Playbook Service',
        data=ansible_service
    )
    assert len(service_classes['Ansible Playbook Service'].query.all()) == 1
    assert len(Service.query.all()) == 14

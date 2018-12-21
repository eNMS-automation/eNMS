from werkzeug.datastructures import ImmutableMultiDict

from eNMS.base.helpers import fetch, fetch_all
from eNMS.base.properties import device_subtypes, link_subtypes

from tests.test_base import check_blueprints


def define_device(subtype, description):
    return ImmutableMultiDict([
        ('name', subtype + description),
        ('type', 'Device'),
        ('description', description),
        ('location', 'paris'),
        ('vendor', 'Cisco'),
        ('type', subtype),
        ('ip_address', '192.168.1.88'),
        ('operating_system', 'IOS'),
        ('os_version', '1.4.4.2'),
        ('longitude', '12'),
        ('latitude', '14'),
        ('secret_password', 'secret_password'),
    ])


def define_link(subtype, source, destination):
    return ImmutableMultiDict([
        ('name', f'{subtype}: {source} to {destination}'),
        ('type', 'Link'),
        ('description', 'description'),
        ('location', 'Los Angeles'),
        ('vendor', 'Juniper'),
        ('type', subtype),
        ('source_name', source),
        ('destination_name', destination),
    ])


def test_manual_object_creation(user_client):
    for subtype in device_subtypes:
        for description in ('desc1', 'desc2'):
            obj_dict = define_device(subtype, description)
            user_client.post('/update/device', data=obj_dict)
    for subtype in link_subtypes:
        devices = fetch_all('Device')
        for source in devices[:3]:
            for destination in devices[:3]:
                obj_dict = define_link(subtype, source.name, destination.name)
                user_client.post('/update/link', data=obj_dict)
    assert len(fetch_all('Device')) == 44
    assert len(fetch_all('Link')) == 82


def create_from_file(client, file):
    with open(client.application.path / 'projects' / file, 'rb') as f:
        data = {'file': f, 'replace': True, 'update_pools': True}
        client.post('/inventory/import_topology', data=data)


@check_blueprints('', '/inventory', '/views')
def test_object_creation_europe(user_client):
    create_from_file(user_client, 'europe.xls')
    assert len(fetch_all('Device')) == 33
    assert len(fetch_all('Link')) == 49


@check_blueprints('', '/inventory', '/views')
def test_object_creation_type(user_client):
    create_from_file(user_client, 'device_counters.xls')
    assert len(fetch_all('Device')) == 27
    assert len(fetch_all('Link')) == 0


routers = ['router' + str(i) for i in range(5, 20)]
links = ['link' + str(i) for i in range(4, 15)]


@check_blueprints('', '/inventory', '/views')
def test_device_deletion(user_client):
    create_from_file(user_client, 'europe.xls')
    for device_name in routers:
        device = fetch('Device', name=device_name)
        user_client.post(f'/delete/device/{device.id}')
    assert len(fetch_all('Device')) == 18
    assert len(fetch_all('Link')) == 18


@check_blueprints('', '/inventory', '/views')
def test_link_deletion(user_client):
    create_from_file(user_client, 'europe.xls')
    for link_name in links:
        link = fetch('Link', name=link_name)
        user_client.post(f'/delete/link/{link.id}')
    assert len(fetch_all('Device')) == 33
    assert len(fetch_all('Link')) == 38


pool1 = ImmutableMultiDict([
    ('name', 'pool1'),
    ('device_location', 'france|spain'),
    ('device_location_regex', 'y'),
    ('link_name', 'link[1|2].'),
    ('link_name_regex', 'y'),
])

pool2 = ImmutableMultiDict([
    ('name', 'pool2'),
    ('device_location', 'france'),
    ('link_name', 'l.*k\\S3'),
    ('link_name_regex', 'y'),
])


@check_blueprints('', '/inventory', '/views')
def test_pool_management(user_client):
    create_from_file(user_client, 'europe.xls')
    user_client.post('/update/pool', data=pool1)
    user_client.post('/update/pool', data=pool2)
    p1, p2 = fetch('Pool', name='pool1'), fetch('Pool', name='pool2')
    assert len(p1.devices) == 21
    assert len(p1.links) == 20
    assert len(p2.devices) == 12
    assert len(p2.links) == 4
    assert len(fetch_all('Pool')) == 5
    user_client.post(f'/delete/pool/{p1.id}')
    user_client.post(f'/delete/pool/{p2.id}')
    assert len(fetch_all('Pool')) == 3

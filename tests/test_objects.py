from test_base import check_blueprints
from conftest import path_projects
from objects.models import (
    Antenna,
    Filter,
    Firewall,
    Host,
    OpticalSwitch,
    Regenerator,
    Router,
    Switch,
    Server,
    BgpPeering,
    Etherchannel,
    EthernetLink,
    OpticalChannel,
    OpticalLink,
    Pseudowire,
    Node,
    node_class,
    Link,
    link_class
)
from os.path import join
from werkzeug.datastructures import ImmutableMultiDict

# test the creation of objects, manual and via excel import
# test the deletion of objects
# test the filtering system

## Object creation


def define_node(subtype, description):
    return ImmutableMultiDict([
        ('name', subtype + description),
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
        ('add_node', '')
    ])


def define_link(subtype, source, destination, name):
    return ImmutableMultiDict([
        ('name', name),
        ('description', 'description'),
        ('location', 'Los Angeles'),
        ('vendor', 'Juniper'),
        ('type', subtype),
        ('source', source),
        ('destination', destination),
        ('add_link', '')
    ])


def test_manual_object_creation(user_client):
    # we create two nodes per type
    for subtype in node_class:
        for description in ('desc1', 'desc2'):
            obj_dict = define_node(subtype, description)
            user_client.post('/objects/edit_object', data=obj_dict)
    # for each type of link, we select the first 3 nodes in the node row
    # and create a link between each pair of nodes (including loopback links)
    for subtype in link_class:
        nodes = Node.query.all()
        for source in nodes[:3]:
            for destination in nodes[:3]:
                name = '{}: {} to {}'.format(subtype, source, destination)
                obj_dict = define_link(subtype, source, destination, name)
                user_client.post('/objects/edit_object', data=obj_dict)
    # there must be:
    for cls in node_class.values():
        # - two nodes per type of nodes
        assert(len(cls.query.all()) == 2)
    # - exactly 16 nodes in total
    assert len(Node.query.all()) == 16
    for cls in link_class.values():
        # - 9 links per type of links (all possible links between 3 nodes)
        assert(len(cls.query.all()) == 9)
    # - exactly 6*9 = 54 links in total
    assert len(Link.query.all()) == 54


def create_from_file(client, file):
    with open(join(path_projects, file), 'rb') as f:
        data = dict(add_nodes='', file=f)
        client.post('/objects/object_management', data=data)


@check_blueprints('', '/objects', '/views')
def test_object_creation_europe(user_client):
    create_from_file(user_client, 'europe.xls')
    assert len(Node.query.all()) == 33
    assert len(Link.query.all()) == 49


@check_blueprints('', '/objects', '/views')
def test_object_creation_type(user_client):
    create_from_file(user_client, 'node_counters.xls')
    assert len(Node.query.all()) == 27
    assert not Link.query.all()


@check_blueprints('', '/objects', '/views')
def test_object_creation_all_type(user_client):
    create_from_file(user_client, 'all_types.xls')
    number_per_subtype = {
        Antenna: 20,
        Firewall: 38,
        Host: 40,
        OpticalSwitch: 32,
        Regenerator: 38,
        Router: 81,
        Switch: 40,
        Server: 60,
        BgpPeering: 13,
        Etherchannel: 155,
        EthernetLink: 103,
        OpticalChannel: 42,
        OpticalLink: 14,
        Pseudowire: 22
    }
    for cls, number in number_per_subtype.items():
        assert len(cls.query.all()) == number

## Object deletion


nodes = ['router' + str(i) for i in range(5, 20)]
links = ['link' + str(i) for i in range(4, 15)]


@check_blueprints('', '/objects', '/views')
def test_node_deletion(user_client):
    create_from_file(user_client, 'europe.xls')
    for node in nodes:
        user_client.post('/objects/delete_node_' + node)
    assert len(Node.query.all()) == 18
    assert len(Link.query.all()) == 18


@check_blueprints('', '/objects', '/views')
def test_link_deletion(user_client):
    create_from_file(user_client, 'europe.xls')
    for link in links:
        user_client.post('/objects/delete_link_' + link)
    assert len(Node.query.all()) == 33
    assert len(Link.query.all()) == 38

## Object filtering


filter1 = ImmutableMultiDict([
    ('name', 'filter1'),
    ('node_location', 'france|spain'),
    ('node_location_regex', 'y'),
    ('link_name', 'link[1|2].'),
    ('link_name_regex', 'y'),
])

filter2 = ImmutableMultiDict([
    ('name', 'filter2'),
    ('node_location', 'france'),
    ('link_name', 'l.*k\\S3'),
    ('link_name_regex', 'y'),
])


@check_blueprints('', '/objects', '/views')
def test_object_filtering(user_client):
    create_from_file(user_client, 'europe.xls')
    user_client.post('/objects/process_filter', data=filter1)
    user_client.post('/objects/process_filter', data=filter2)
    assert len(Filter.query.all()) == 5

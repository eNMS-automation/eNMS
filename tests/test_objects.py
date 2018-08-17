from tests.test_base import check_blueprints
from eNMS.objects.models import (
    Antenna,
    get_obj,
    Pool,
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
# test the pool system

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
                name = f'{subtype}: {source.name} to {destination.name}'
                obj_dict = define_link(subtype, source.id, destination.id, name)
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
    with open(join(client.application.path, 'projects', file), 'rb') as f:
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
    for node_name in nodes:
        node = get_obj(Node, name=node_name)
        user_client.post('/objects/delete/node/{}'.format(node.id))
    assert len(Node.query.all()) == 18
    assert len(Link.query.all()) == 18


@check_blueprints('', '/objects', '/views')
def test_link_deletion(user_client):
    create_from_file(user_client, 'europe.xls')
    for link_name in links:
        link = get_obj(Link, name=link_name)
        user_client.post('/objects/delete/link/{}'.format(link.id))
    assert len(Node.query.all()) == 33
    assert len(Link.query.all()) == 38

## Pool management


pool1 = ImmutableMultiDict([
    ('name', 'pool1'),
    ('node_location', 'france|spain'),
    ('node_location_regex', 'y'),
    ('link_name', 'link[1|2].'),
    ('link_name_regex', 'y'),
])

pool2 = ImmutableMultiDict([
    ('name', 'pool2'),
    ('node_location', 'france'),
    ('link_name', 'l.*k\\S3'),
    ('link_name_regex', 'y'),
])


@check_blueprints('', '/objects', '/views')
def test_pool_management(user_client):
    create_from_file(user_client, 'europe.xls')
    user_client.post('/objects/process_pool', data=pool1)
    user_client.post('/objects/process_pool', data=pool2)
    p1, p2 = get_obj(Pool, name='pool1'), get_obj(Pool, name='pool2')
    assert len(p1.nodes) == 21
    assert len(p1.links) == 20
    assert len(p2.nodes) == 12
    assert len(p2.links) == 4
    assert len(Pool.query.all()) == 5
    user_client.post('/objects/delete_pool/{}'.format(p1.id))
    user_client.post('/objects/delete_pool/{}'.format(p2.id))
    assert len(Pool.query.all()) == 3

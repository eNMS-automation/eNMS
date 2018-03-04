from test_base import check_blueprints
from conftest import path_projects
from objects.models import *
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
            r = user_client.post('/objects/object_creation', data=obj_dict)
    # for each type of link, we select the first 3 nodes in the node row
    # and create a link between each pair of nodes (including loopback links)
    for subtype in link_class:
        nodes = Node.query.all()
        for source in nodes[:3]:
            for destination in nodes[:3]:
                name = '{}: {} to {}'.format(subtype, source, destination)
                obj_dict = define_link(subtype, source, destination, name)
                r = user_client.post('/objects/object_creation', data=obj_dict)
    # there must be 
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
        res = client.post('/objects/object_creation', data=data)

@check_blueprints('/', '/objects/', '/views/')
def test_object_creation_europe(user_client):
    create_from_file(user_client, 'europe.xls')
    assert len(Node.query.all()) == 33
    assert len(Link.query.all()) == 49

@check_blueprints('/', '/objects/', '/views/')
def test_object_creation_type(user_client):
    create_from_file(user_client, 'node_counters.xls')
    assert len(Node.query.all()) == 27
    assert not Link.query.all()

@check_blueprints('/', '/objects/', '/views/')
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

nodes = ImmutableMultiDict([('nodes', 'router' + str(i)) for i in range(5, 20)])
links = ImmutableMultiDict([('links', 'link' + str(i)) for i in range(4, 15)])

@check_blueprints('/', '/objects/', '/views/')
def test_node_deletion(user_client):
    create_from_file(user_client, 'europe.xls')
    res = user_client.post('/objects/object_deletion', data=nodes)
    assert len(Node.query.all()) == 18
    assert len(Link.query.all()) == 18

@check_blueprints('/', '/objects/', '/views/')
def test_link_deletion(user_client):
    create_from_file(user_client, 'europe.xls')
    res = user_client.post('/objects/object_deletion', data=links)
    assert len(Node.query.all()) == 33
    assert len(Link.query.all()) == 38

## Object filtering

filter_objects1 = ImmutableMultiDict([
    ('nodelocation', 'france|spain'),
    ('nodelocationregex', 'y'),
    ('linkname', 'link[1|2].'),
    ('linknameregex', 'y'),
    ])

filter_objects2 = ImmutableMultiDict([
    ('nodelocation', 'france'),
    ('linkname', 'l.*k\\S3'),
    ('linknameregex', 'y'),
    ])

@check_blueprints('/', '/objects/', '/views/')
def test_object_filtering(user_client):
    create_from_file(user_client, 'europe.xls')
    res = user_client.post('/objects/object_filtering', data=filter_objects1)
    assert len(Node.visible_choices()) == 21
    assert len(Link.visible_choices()) == 20
    res = user_client.post('/objects/object_filtering', data=filter_objects2)
    assert len(Node.visible_choices()) == 12
    assert len(Link.visible_choices()) == 4
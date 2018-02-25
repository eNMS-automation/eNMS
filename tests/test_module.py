from werkzeug.datastructures import ImmutableMultiDict
from objects.models import *

urls = {
    '/': (
        '',
        'dashboard',
        'dashboard_control',
        'project'
        ),
    '/users/': (
        'overview',
        'manage_users',
        'login',
        'create_account',
        'tacacs_server'
        ),
    '/objects/': (
        'objects',
        'object_creation',
        'object_deletion',
        'object_filtering'
        ),
    '/views/': (
        'geographical_view',
        'logical_view',
        'google_earth_export'
        ),
    '/scripts/': (
        'overview',
        'script_creation',
        'ansible_script'
        ),
    '/tasks/': (
        'task_management',
        'calendar'
        ),
    '/logs/': (
        'overview',
        'syslog_server'
        )
    }

free_access = {'/', '/users/login', '/users/create_account'}

## Base test
# test the login system: login, user creation, logout
# test that all pages respond with HTTP 403 if not logged in, 200 otherwise

def test_authentication(base_client):
    for blueprint, pages in urls.items():
        for page in pages:
            page_url = blueprint + page
            expected_code = 200 if page_url in free_access else 403
            r = base_client.get(page_url, follow_redirects=True)
            assert r.status_code == expected_code

def test_urls(user_client):
    for blueprint, pages in urls.items():
        for page in pages:
            page_url = blueprint + page
            r = user_client.get(page_url, follow_redirects=True)
            assert r.status_code == 200
    # logout and test that we cannot access anything anymore
    r = user_client.get('/users/logout', follow_redirects=True)
    test_authentication(user_client)

## Objects 
# test the creation of objects, manual and via excel import
# test the deletion of objects
# test the filtering system

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

from test_base import check_blueprints
from conftest import path_scripts
from os.path import join
from werkzeug.datastructures import ImmutableMultiDict

# test the creation of standard script (netmiko / napalm)
# test the creation of ansible script

## Standard scripts

simple_script = ImmutableMultiDict([
    ('name', 'ping'),
    ('type', 'simple'),
    ('create_script', ''),
    ('text', 'ping 1.1.1.1')
    ])

@check_blueprints('/scripts/')
def test_simple_script(user_client):
    res = user_client.post('/scripts/script_creation', data=simple_script)
    assert len(Script.query.all()) == 18
    assert len(Link.query.all()) == 18

# def create_from_file(client, file):
#     with open(join(path_projects, file), 'rb') as f:
#         data = dict(add_nodes='', file=f)
#         res = client.post('/objects/object_creation', data=data)
# 
# @check_blueprints('/', '/objects/', '/views/')
# def test_object_creation_europe(user_client):
#     create_from_file(user_client, 'europe.xls')
#     assert len(Node.query.all()) == 33
#     assert len(Link.query.all()) == 49
# 
# @check_blueprints('/', '/objects/', '/views/')
# def test_object_creation_type(user_client):
#     create_from_file(user_client, 'node_counters.xls')
#     assert len(Node.query.all()) == 27
#     assert not Link.query.all()




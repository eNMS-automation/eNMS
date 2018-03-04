from base.database import db
from conftest import path_scripts
from os.path import join
from scripts.models import *
from test_base import check_blueprints
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

jinja2_script = dict([
    ('name', 'subif'), 
    ('type', 'j2_template'),
    ('create_script', ''),
    ('text', template)
    ])

@check_blueprints('/scripts/')
def test_simple_script(user_client):
    res = user_client.post('/scripts/script_creation', data=simple_script)
    assert len(ClassicScript.query.all()) == 1
    path_yaml = join(path_scripts, 'cisco', 'interfaces', 'parameters.yaml')
    with open(path_yaml, 'rb') as f:
        jinja2_script['file'] = f
        res = user_client.post('/scripts/script_creation', data=jinja2_script)
    assert len(ClassicScript.query.all()) == 2
    j2_script = db.session.query(Script).filter_by(name='subif').first()
    assert ''.join(j2_script.content.split()) == ''.join(result.split())

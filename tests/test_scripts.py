from base.database import db
from conftest import path_playbooks, path_projects, path_scripts
from os import remove
from os.path import join
from scripts.models import (
    AnsibleScript,
    ConfigScript,
    FileTransferScript,
    Script
)
from test_base import check_blueprints
from werkzeug.datastructures import ImmutableMultiDict

# test the creation of configuration script (netmiko / napalm)
# test the creation of file transfer script (netmiko via SCP)
# test the creation of ansible script

## Standard scripts (configuration, file transfer)

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

file_transfer_script = ImmutableMultiDict([
    ('name', 'test'),
    ('driver', 'cisco_ios'),
    ('source_file', 'path/to/source'),
    ('destination_file', 'path/to/destination'),
    ('file_system', 'flash:'),
    ('direction', 'put'),
    ('create_script', ''),
])


@check_blueprints('/scripts')
def test_base_scripts(user_client):
    ## configuration script (simple, Jinja2)
    user_client.post('/scripts/configuration_script', data=simple_script)
    assert len(ConfigScript.query.all()) == 1
    path_yaml = join(path_scripts, 'cisco', 'interfaces', 'parameters.yaml')
    with open(path_yaml, 'rb') as f:
        jinja2_script['file'] = f
        user_client.post('/scripts/configuration_script', data=jinja2_script)
    assert len(ConfigScript.query.all()) == 2
    j2_script = db.session.query(Script).filter_by(name='subif').first()
    # simply removing the space does not work as yaml relies on dict, which
    # are not ordered, we use set instead for the test to pass on python 2 and 3
    assert set(j2_script.content.split('\n')) == set(result.split('\n'))
    ## file transfer script
    user_client.post('scripts/file_transfer_script', data=file_transfer_script)
    assert len(FileTransferScript.query.all()) == 1
    assert len(Script.query.all()) == 3


## Ansible script

ansible_script = {
    'name': 'ansible_test',
    'listtags': 'False',
    'listtasks': 'False',
    'listhosts': 'False',
    'syntax': 'False',
    'connection': 'ssh',
    'module_path': '',
    'forks': '100',
    'remote_user': '',
    'private_key_file': '',
    'ssh_common_args': '',
    'ssh_extra_args': '',
    'sftp_extra_args': '',
    'scp_extra_args': '',
    'become': 'False',
    'become_method': '',
    'become_user': '',
    'verbosity': '',
    'check': 'False',
    'diff': 'False'
}


@check_blueprints('/scripts')
def test_ansible_scripts(user_client):
    path_yaml = join(path_playbooks, 'save_running_config.yml')
    with open(path_yaml, 'rb') as f:
        ansible_script['file'] = f
        user_client.post('/scripts/ansible_script', data=ansible_script)
    assert len(AnsibleScript.query.all()) == 1
    assert len(Script.query.all()) == 1
    # the playbook is saved in /projects, we delete it at the end of the test
    remove(join(path_projects, 'save_running_config.yml'))
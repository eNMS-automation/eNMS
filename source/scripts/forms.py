from collections import OrderedDict
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from netmiko.ssh_dispatcher import CLASS_MAPPER as netmiko_dispatcher
from wtforms import (
    BooleanField,
    FileField,
    FloatField,
    IntegerField,
    SelectField,
    SelectMultipleField,
    TextAreaField,
    TextField
)

getters_mapping = OrderedDict([
    ('ARP table', 'get_arp_table'),
    ('Interfaces counters', 'get_interfaces_counters'),
    ('Facts', 'get_facts'),
    ('Environment', 'get_environment'),
    ('Configuration', 'get_config'),
    ('Interfaces', 'get_interfaces'),
    ('Interface IP', 'get_interfaces_ip'),
    ('LLDP neighbors', 'get_lldp_neighbors'),
    ('LLDP neighbors detail', 'get_lldp_neighbors_detail'),
    ('MAC address', 'get_mac_address_table'),
    ('NTP servers', 'get_ntp_servers'),
    ('NTP statistics', 'get_ntp_stats'),
    ('Transceivers', 'get_optics'),
    ('SNMP', 'get_snmp_information'),
    ('Users', 'get_users'),
    ('Network instances (VRF)', 'get_network_instances'),
    ('NTP peers', 'get_ntp_peers'),
    ('BGP configuration', 'get_bgp_config'),
    ('BGP neighbors', 'get_bgp_neighbors'),
    ('IPv6', 'get_ipv6_neighbors_table'),
])

napalm_actions = OrderedDict([
    ('Load merge', 'load_merge_candidate'),
    ('Load replace', 'load_replace_candidate'),
    ('Commit', 'commit_config'),
    ('Discard', 'discard_config'),
    ('Rollback', 'rollback'),
])

ansible_options = {
    'listtags': ('List of tags', False),
    'listtasks': ('List of tasks', False),
    'listhosts': ('List of hosts', False),
    'syntax': ('Syntax', False),
    'connection': ('Connection', 'ssh'),
    'module_path': ('Module path', None),
    'forks': ('Number of forks', 100),
    'remote_user': ('Remote user', None),
    'private_key_file': ('Private key file', None),
    'ssh_common_args': ('SSH common arguments', None),
    'ssh_extra_args': ('SSH extra arguments', None),
    'sftp_extra_args': ('SFTP extra arguments', None),
    'scp_extra_args': ('SCP extra arguments', None),
    'become': ('Become', False),
    'become_method': ('Become method', None),
    'become_user': ('Become user', None),
    'verbosity': ('Verbosity', None),
    'check': ('Check', False),
    'diff': ('Diff', False)
}

class ScriptForm(FlaskForm):
    name = TextField('Name')


class ConfigScriptForm(ScriptForm):
    text = TextAreaField('')
    file = FileField('', validators=[FileAllowed(['yaml'], 'YAML only')])
    content_type_choices = (
        ('simple', 'Simple'),
        ('j2_template', 'Jinja2 template')
    )
    content_type = SelectField('', choices=content_type_choices)


class NetmikoConfigScriptForm(ConfigScriptForm):

    text = TextAreaField('')
    file = FileField('', validators=[FileAllowed(['yaml'], 'YAML only')])
    type_choices = (
        ('show_commands', 'Show commands'),
        ('configuration', 'Configuration')
    )
    type = SelectField('', choices=type_choices)
    # exclude base driver from Netmiko available drivers
    exclude_base_driver = lambda driver: 'telnet' in driver or 'ssh' in driver
    netmiko_drivers = sorted(tuple(filter(exclude_base_driver, netmiko_dispatcher)))
    drivers = [(driver, driver) for driver in netmiko_drivers]
    driver = SelectField('', choices=drivers)
    global_delay_factor = FloatField('global_delay_factor', default=1.)


class NapalmConfigScriptForm(ConfigScriptForm):
    action_choices = [(v, k) for k, v in napalm_actions.items()]
    actions = SelectField('Actions', choices=action_choices)


class NapalmGettersForm(FlaskForm):
    getters_choices = [(v, k) for k, v in getters_mapping.items()]
    getters = SelectMultipleField('Nodes', choices=getters_choices)


class FileTransferScriptForm(ScriptForm):
    name = TextField('Name')
    driver_choices = (
        ('cisco_ios', 'Cisco IOS'),
        ('cisco_xe', 'Cisco IOS-XE'),
        ('cisco_xr', 'Cisco IOS-XR'),
        ('cisco_nxos', 'Cisco NX-OS'),
        ('juniper_junos', 'Juniper'),
        ('arista_eos', 'Arista')
    )
    driver = SelectField('', choices=driver_choices)
    source_file = TextField('Source file')
    destination_file = TextField('Destination file')
    file_system = TextField('File system')
    direction_choices = (('put', 'Upload'), ('get', 'Download'))
    direction = SelectField('', choices=direction_choices)
    overwrite_file = BooleanField()
    disable_md5 = BooleanField()
    inline_transer = BooleanField()


def configure_form(cls):
    for option, (pretty_name, default_value) in ansible_options.items():
        setattr(cls, option, TextField(pretty_name, default=default_value))
    return cls


@configure_form
class AnsibleScriptForm(ScriptForm):
    name = TextField('Name')


class WorkflowCreationForm(ScriptForm):
    name = TextField('Name')
    netmiko_scripts = SelectField('', choices=())
    napalm_scripts = SelectField('', choices=())
    ansible_scripts = SelectField('', choices=())

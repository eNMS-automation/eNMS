from collections import OrderedDict
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from netmiko.ssh_dispatcher import CLASS_MAPPER as netmiko_dispatcher
from scheduling.forms import SchedulingForm
from wtforms import *
from wtforms.validators import Length, optional

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

## Script creation

class ScriptCreationForm(FlaskForm):
    name = TextField('Name')
    type_choices = (
        ('simple', 'Simple'),
        ('j2_template', 'Jinja2 template'),
        ('per_device_j2', 'Per-device Jinja2 template')
        )
    type = SelectField('', [optional()], choices=type_choices)
    text = TextAreaField('', [optional(), Length(max=200)])
    file = FileField('', validators=[FileAllowed(['yaml'], 'YAML only')])

## Forms for Netmiko
    
class NetmikoForm(SchedulingForm):
    script = SelectField('', [optional()], choices=())
    nodes = SelectMultipleField('', [optional()], choices=())
    type_choices = (
        ('show_commands', 'Show commands'),
        ('configuration', 'Configuration')
        )
    type = SelectField('', choices=type_choices)
    # exclude base driver from Netmiko available drivers
    exclude_base_driver = lambda driver: 'telnet' in driver or 'ssh' in driver
    netmiko_drivers = sorted(tuple(filter(exclude_base_driver, netmiko_dispatcher)))
    drivers = [(driver, driver) for driver in netmiko_drivers]
    driver = SelectField('', [optional()], choices=drivers)
    global_delay_factor = FloatField('global_delay_factor', [optional()], default=1.)
    nodes = SelectMultipleField('Nodes', choices=())
    
## Forms for NAPALM

class NapalmGettersForm(SchedulingForm):
    nodes = SelectMultipleField('', [optional()], choices=())
    getters_choices = [(v, k) for k, v in getters_mapping.items()]
    getters = SelectMultipleField('Nodes', choices=getters_choices)
    output = TextAreaField('', [optional()])

class NapalmConfigurationForm(SchedulingForm):
    script = SelectField('', [optional()], choices=())
    nodes = SelectMultipleField('', [optional()], choices=())
    action_choices = [(v, k) for k, v in napalm_actions.items()]
    actions = SelectField('Actions', [optional()], choices=action_choices)
    nodes = SelectMultipleField('Nodes', choices=())
    
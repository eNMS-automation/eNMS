from base.properties import pretty_names
from collections import OrderedDict
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from netmiko.ssh_dispatcher import CLASS_MAPPER as netmiko_dispatcher
from objects.properties import node_public_properties, link_public_properties
from wtforms import *
from wtforms.validators import Length

class ViewOptionsForm(FlaskForm):
    node_label_choices = [(p, pretty_names[p]) for p in node_public_properties]
    node_label = SelectField('Actions', choices=node_label_choices)
    link_label_choices = [(p, pretty_names[p]) for p in link_public_properties]
    link_label = SelectField('Actions', choices=link_label_choices)

class GoogleEarthForm(FlaskForm):
    name = TextField('Project name')
    label_size = IntegerField('Label size', default=1)
    line_width = IntegerField('Line width', default=2)

## Automation

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

class SchedulingForm(FlaskForm):
    scheduled_date = TextField('Datetime')
    name = TextField('Name')
    script = SelectField('', choices=())
    frequency = TextField('Frequency')

## Netmiko automation

class NetmikoForm(SchedulingForm):
    script = SelectField('', choices=())
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

## NAPALM automation

class NapalmGettersForm(SchedulingForm):
    getters_choices = [(v, k) for k, v in getters_mapping.items()]
    getters = SelectMultipleField('Nodes', choices=getters_choices)
    output = TextAreaField('')

class NapalmConfigurationForm(SchedulingForm):
    script = SelectField('', choices=())
    action_choices = [(v, k) for k, v in napalm_actions.items()]
    actions = SelectField('Actions', choices=action_choices)

class AnsibleForm(SchedulingForm):
    pass
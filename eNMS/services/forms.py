from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from netmiko.ssh_dispatcher import CLASS_MAPPER
from wtforms import (
    BooleanField,
    FileField,
    FloatField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    TextAreaField,
    TextField
)

getters_mapping = {
    'ARP table': 'get_arp_table',
    'Interfaces counters': 'get_interfaces_counters',
    'Facts': 'get_facts',
    'Environment': 'get_environment',
    'Configuration': 'get_config',
    'Interfaces': 'get_interfaces',
    'Interface IP': 'get_interfaces_ip',
    'LLDP neighbors': 'get_lldp_neighbors',
    'LLDP neighbors detail': 'get_lldp_neighbors_detail',
    'MAC address': 'get_mac_address_table',
    'NTP servers': 'get_ntp_servers',
    'NTP statistics': 'get_ntp_stats',
    'Transceivers': 'get_optics',
    'SNMP': 'get_snmp_information',
    'Users': 'get_users',
    'Network instances (VRF)': 'get_network_instances',
    'NTP peers': 'get_ntp_peers',
    'BGP configuration': 'get_bgp_config',
    'BGP neighbors': 'get_bgp_neighbors',
    'IPv6': 'get_ipv6_neighbors_table'
}

napalm_actions = {
    'Load merge': 'load_merge_candidate',
    'Load replace': 'load_replace_candidate'
}

netmiko_drivers = sorted(
    driver for driver in CLASS_MAPPER
    if 'telnet' not in driver and 'ssh' not in driver
)


class ServiceForm(FlaskForm):
    name = TextField('Name')
    description = TextField('Description')


class ConfigServiceForm(ServiceForm):
    vendor = TextField('Vendor')
    operating_system = TextField('Operating system')
    content = TextAreaField('')
    file = FileField('', validators=[FileAllowed(['yaml'], 'YAML only')])


class NapalmConfigServiceForm(ConfigServiceForm):
    action_choices = [(v, k) for k, v in napalm_actions.items()]
    action = SelectField('Actions', choices=action_choices)


class NapalmGettersForm(ServiceForm):
    getters_choices = [(v, k) for k, v in getters_mapping.items()]
    getters = SelectMultipleField('Getters', choices=getters_choices)
    content_match = TextField('Content Match')
    content_match_regex = BooleanField()


class AnsibleServiceForm(ServiceForm):
    vendor = TextField('Vendor')
    operating_system = TextField('Operating system')
    playbook_path = TextField('Path to playbook')
    arguments = TextField('Optional arguments')
    inventory_from_selection = BooleanField()
    content_match = TextField('Content Match')
    content_match_regex = BooleanField()
    pass_device_properties = BooleanField()


class RestCallServiceForm(ServiceForm):
    choices = ('GET', 'POST', 'PUT', 'DELETE')
    call_type = SelectField('Type', choices=tuple(zip(choices, choices)))
    url = TextField('URL')
    payload = TextAreaField('Payload')
    username = TextField('Username')
    password = PasswordField('Password')
    content_match = TextField('Content Match')
    content_match_regex = BooleanField()

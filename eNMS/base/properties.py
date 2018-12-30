from os import environ
from sqlalchemy import Boolean, Integer, String, Float
from yaml import load


def get_custom_properties():
    filepath = environ.get('PATH_CUSTOM_PROPERTIES')
    if not filepath:
        return {}
    with open(filepath, 'r') as properties:
        return load(properties)


sql_types = {
    'boolean': Boolean,
    'float': Float,
    'integer': Integer,
    'string': String
}

custom_properties = get_custom_properties()
boolean_properties = [
    'mattermost_verify_certificate',
    'multiprocessing',
    'send_notification',
    'use_workflow_targets',
    'push_to_git'
]
list_properties = [
    'devices',
    'pools',
    'links',
    'permissions',
    'getters',
    'import_export_types'
]
private_properties = ['password', 'enable_password']

base_properties = [
    'id',
    'name',
    'description'
]

object_common_properties = base_properties + [
    'subtype',
    'model',
    'location',
    'vendor'
]

device_subtypes = {
    'antenna': 'Antenna',
    'firewall': 'Firewall',
    'host': 'Host',
    'optical_switch': 'Optical switch',
    'regenerator': 'Regenerator',
    'router': 'Router',
    'server': 'Server',
    'switch': 'Switch'
}

link_subtypes = {
    'bgp_peering': 'BGP peering',
    'etherchannel': 'Etherchannel',
    'ethernet_link': 'Ethernet link',
    'optical_channel': 'Optical channel',
    'optical_link': 'Optical link',
    'pseudowire': 'Pseudowire'
}

link_subtype_to_color = {
    'bgp_peering': '#77ebca',
    'etherchannel': '#cf228a',
    'ethernet_link': '#0000ff',
    'optical_link': '#d4222a',
    'optical_channel': '#ff8247',
    'pseudowire': '#902bec'
}

device_table_properties = object_common_properties[1:] + [
    'operating_system',
    'os_version',
    'netmiko_driver',
    'napalm_driver',
    'ip_address',
    'port'
] + list(custom_properties)

device_public_properties = device_table_properties + [
    'longitude',
    'latitude',
    'username',
    'configuration_command',
    'last_failure',
    'last_runtime',
    'last_status',
    'last_update'
]

device_configuration_properties = [
    'name',
    'configuration_command',
    'last_failure',
    'last_runtime',
    'last_update',
    'last_status'
]

task_properties = base_properties + [
    'job_name',
    'start_date',
    'end_date',
    'frequency',
    'status'
]

task_public_properties = task_properties[1:]

link_properties = object_common_properties + [
    'source',
    'destination',
]

link_public_properties = link_properties[1:] + [
    'source_name',
    'destination_name'
]

link_table_properties = object_common_properties[1:] + [
    'source_name',
    'destination_name'
]

pool_table_properties = base_properties[1:]

pool_public_properties = base_properties[1:]

for obj_type, properties in (
    ('device', device_public_properties),
    ('link', link_public_properties)
):
    for prop in properties:
        pool_public_properties.extend([
            f'{obj_type}_{prop}',
            f'{obj_type}_{prop}_regex'
        ])
        boolean_properties.append(f'{obj_type}_{prop}_regex')


job_public_properties = [
    'name',
    'multiprocessing',
    'vendor',
    'operating_system',
    'type',
    'description',
    'creator_name',
    'credentials',
    'status',
    'state',
    'positions',
    'push_to_git',
    'waiting_time',
    'number_of_retries',
    'time_between_retries',
    'send_notification',
    'send_notification_method'
]

service_public_properties = job_public_properties
workflow_public_properties = job_public_properties + [
    'last_modified',
    'use_workflow_targets'
]

service_table_properties = [
    'name',
    'type',
    'description',
    'creator_name',
    'number_of_retries',
    'time_between_retries',
    'status'
]

workflow_table_properties = [
    'name',
    'description',
    'creator_name',
    'vendor',
    'operating_system',
    'number_of_retries',
    'time_between_retries',
    'status'
]

workflow_edge_properties = [
    'name',
    'subtype',
    'source_id',
    'destination_id'
]

user_public_properties = [
    'name',
    'email'
]

user_serialized_properties = [
    'name',
    'email',
    'permissions'
]

instance_public_properties = [
    'name',
    'description',
    'ip_address',
    'weight',
    'status',
    'cpu_load'
]

user_permissions = [
    'Admin',
    'Connect to device',
    'View',
    'Edit'
]

log_public_properties = [
    'source_ip',
    'content'
]

log_rule_public_properties = log_public_properties + [
    'name',
    'source_ip_regex',
    'content_regex',
    'jobs'
]

parameters_public_properties = [
    'cluster_scan_subnet',
    'cluster_scan_protocol',
    'cluster_scan_timeout',
    'default_longitude',
    'default_latitude',
    'default_zoom_level',
    'default_view',
    'git_repository_configurations',
    'git_repository_automation',
    'gotty_start_port',
    'gotty_end_port',
    'mail_sender',
    'mail_recipients',
    'mattermost_url',
    'mattermost_channel',
    'mattermost_verify_certificate',
    'opennms_rest_api',
    'opennms_devices',
    'opennms_login',
    'pool'
]

task_serialized_properties = [
    'id',
    'name',
    'description',
    'job_name',
    'status',
    'start_date',
    'end_date',
    'frequency'
]

cls_to_properties = {
    'Instance': instance_public_properties,
    'Device': device_public_properties,
    'Link': link_public_properties,
    'Pool': pool_public_properties,
    'Service': service_public_properties,
    'Parameters': parameters_public_properties,
    'Workflow': workflow_public_properties,
    'WorkflowEdge': workflow_edge_properties,
    'User': user_serialized_properties,
    'Log': log_public_properties,
    'LogRule': log_rule_public_properties,
    'Task': task_serialized_properties
}

cls_to_properties = {k: ['id'] + v for k, v in cls_to_properties.items()}

default_diagrams_properties = {
    'Device': 'model',
    'Link': 'model',
    'User': 'name',
    'Service': 'type',
    'Workflow': 'vendor',
    'Task': 'type'
}

object_diagram_properties = [
    'model',
    'vendor',
    'subtype',
    'location'
]

device_diagram_properties = object_diagram_properties + [
    'operating_system',
    'os_version'
] + list(p for p, v in custom_properties.items() if v['add_to_dashboard'])

user_diagram_properties = [
    'name',
]

workflow_diagram_properties = [
    'type',
    'vendor',
    'operating_system'
]

service_diagram_properties = [
    'type',
    'device_multiprocessing'
]

task_diagram_properties = [
    'type',
    'status',
    'frequency'
]

type_to_diagram_properties = {
    'Device': device_diagram_properties,
    'Link': object_diagram_properties,
    'User': user_diagram_properties,
    'Service': service_diagram_properties,
    'Workflow': workflow_diagram_properties,
    'Task': task_diagram_properties
}

pretty_names = {
    'access_rights': 'Access rights',
    'action': 'Action',
    'call_type': 'Type of call',
    'command': 'Command',
    'content': 'Content',
    'content_match': 'Content Match',
    'content_match_regex': 'Match content against Regular expression',
    'content_type': 'Content type',
    'cpu_load': 'CPU load',
    'creator': 'Creator',
    'delete_archive': 'Delete archive',
    'delete_folder': 'Delete folder',
    'delete_spaces_before_matching': 'Delete spaces before matching',
    'description': 'Description',
    'destination': 'Destination',
    'destination_file': 'Destination file',
    'destination_name': 'Destination',
    'destination_path': 'Destination path',
    'dest_file': 'Destination file',
    'device_multiprocessing': 'Device multiprocessing',
    'dict_match': 'Dictionnary match',
    'direction': 'Direction',
    'driver': 'Driver',
    'email': 'Email',
    'enable_mode': 'Enter "Enable" mode',
    'fast_cli': 'Fast CLI',
    'file': 'File',
    'file_system': 'File system',
    'frequency': 'Frequency',
    'getters': 'Getters',
    'global_delay_factor': 'Global delay factor',
    'has_targets': 'Has targets',
    'headers': 'Headers',
    'inventory_from_selection': 'Inventory from selection',
    'ip_address': 'IP address',
    'longitude': 'Longitude',
    'latitude': 'Latitude',
    'load_known_host_keys': 'Load known host keys',
    'location': 'Location',
    'look_for_keys': 'Look for keys',
    'missing_host_key_policy': 'Missing Host Key Policy',
    'model': 'Model',
    'name': 'Name',
    'negative_logic': 'Negative Logic',
    'netmiko_driver': 'Netmiko driver',
    'napalm_driver': 'Napalm driver',
    'number_of_configuration': 'Number of configurations stored',
    'operating_system': 'Operating System',
    'optional_args': 'Optional arguments',
    'os_version': 'OS version',
    'params': 'Parameters',
    'pass_device_properties': 'Pass device properties to the playbook',
    'password': 'Password',
    'payload': 'Payload',
    'permission': 'Permission',
    'port': 'Port',
    'positions': 'Positions',
    'protocol': 'Protocol',
    'recurrent': 'Recurrent',
    'enable_password': 'Enable password',
    'source': 'Source',
    'source_name': 'Source',
    'source_file': 'Source file',
    'source_ip': 'Source IP address',
    'status': 'Status',
    'subtype': 'Subtype',
    'text file': 'File',
    'timeout': 'Timeout (in seconds)',
    'type': 'Type',
    'update_dictionnary': 'Update dictionnary',
    'url': 'URL',
    'use_device_driver': 'Use driver from device',
    'username': 'Username',
    'validation_method': 'Validation Method',
    'vendor': 'Vendor',
    'waiting_time': 'Waiting time',
    'weight': 'Weight'
}

# Import properties

pretty_names.update({k: v['pretty_name'] for k, v in custom_properties.items()})
reverse_pretty_names = {v: k for k, v in pretty_names.items()}

property_types = {
    'devices': 'object-list',
    'links': 'object-list',
    'pools': 'object-list',
    'jobs': 'object-list',
    'edges': 'object-list',
    'permissions': 'list',
    'source': 'object',
    'destination': 'object',
    'import_export_types': 'list',
    'send_notification': 'bool',
    'multiprocessing': 'bool',
    'use_workflow_targets': 'bool',
    'mattermost_verify_certificate': 'bool',
    'push_to_git': 'bool'
}

relationships = {
    'Device': {
        'job': 'Job'
    },
    'Link': {
        'source': 'Device',
        'destination': 'Device'
    },
    'Pool': {
        'device': 'Device',
        'link': 'Link'
    },
    'Service': {
        'creator': 'User',
        'device': 'Device',
        'pool': 'Pool',
        'workflow': 'Workflow',
        'task': 'Task'
    },
    'Task': {
        'job': 'Job'
    },
    'Workflow': {
        'creator': 'User',
        'edge': 'WorkflowEdge',
        'job': 'Job',
        'device': 'Device',
        'pool': 'Pool'
    },
    'WorkflowEdge': {
        'source': 'Job',
        'destination': 'Job',
        'workflow': 'Workflow'
    },
    'Parameters': {
        'pool': 'Pool'
    },
    'LogRule': {
        'job': 'Job',
        'log': 'Log'
    }
}

device_import_properties = device_public_properties + [
    'id'
]

link_import_properties = link_properties + [
    'id'
]

pool_import_properties = pool_public_properties + [
    'id',
    'devices'
]

service_import_properties = service_public_properties + [
    'id',
    'type',
    'devices',
    'pools'
]

task_import_properties = base_properties + [
    'start_date',
    'end_date',
    'frequency',
    'status',
    'job'
]

user_import_properties = user_serialized_properties + [
    'id'
]

workflow_import_properties = workflow_public_properties + [
    'id',
    'jobs',
    'edges'
]

workflow_edge_import_properties = [
    'id',
    'name',
    'subtype',
    'source_id',
    'destination_id',
    'workflow'
]

import_properties = {
    'User': user_import_properties,
    'Device': device_import_properties,
    'Link': link_import_properties,
    'Pool': pool_import_properties,
    'Service': service_import_properties,
    'Workflow': workflow_import_properties,
    'WorkflowEdge': workflow_edge_import_properties,
    'Task': task_import_properties
}

# Export topology properties

export_properties = {
    'Device': device_public_properties,
    'Link': link_table_properties
}

# Properties to not migrate

dont_migrate = {
    'Device': ['jobs'],
    'Service': ['logs', 'state', 'tasks', 'workflows', 'creator_name'],
    'Task': ['job_name'],
    'Workflow': ['last_modified', 'logs', 'state', 'status', 'creator_name']
}

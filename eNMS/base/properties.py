object_common_properties = (
    'name',
    'subtype',
    'description',
    'model',
    'location',
    'vendor'
)

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

device_common_properties = (
    'operating_system',
    'os_version',
    'ip_address',
    'longitude',
    'latitude',
    'enable_password'
)

task_public_properties = (
    'name',
    'creation_time',
    'frequency',
    'status'
)

link_common_properties = (
    'source',
    'destination',
)

device_public_properties = (
    object_common_properties +
    device_common_properties[:-1]
)

link_public_properties = (
    object_common_properties +
    link_common_properties
)

pool_public_properties = (
    'name',
    'description'
)

service_public_properties = (
    'name',
    'type',
    'description'
)

workflow_public_properties = (
    'name',
    'description',
    'vendor',
    'operating_system',
    'type',
    'start_task',
    'end_task'
)

workflow_table_properties = (
    'name',
    'description',
    'vendor',
    'operating_system'
)

workflow_edge_properties = (
    'name',
    'type'
)

user_public_properties = (
    'name',
    'email'
)

user_serialized_properties = (
    'name',
    'email',
    'permissions'
)

user_permissions = (
    'Admin',
    'Admin section',
    'Connect to device',
    'Inventory section',
    'Views section',
    'Services section',
    'Workflows section',
    'Tasks section',
    'Edit logs',
    'Edit parameters',
    'Edit users',
    'Edit objects',
    'Edit services',
    'Edit workflows',
    'Edit tasks',
    'Schedule tasks'
)

log_public_properties = (
    'source',
    'content'
)

log_rule_public_properties = log_public_properties + (
    'name',
    'sourceregex',
    'contentregex'
)

parameters_public_properties = (
    'default_longitude',
    'default_latitude',
    'default_zoom_level',
    'gotty_start_port',
    'gotty_end_port',
    'opennms_rest_api',
    'opennms_devices'
)

task_serialized_properties = (
    'id',
    'name',
    'creation_time',
    'status',
    'logs',
    'start_date',
    'end_date',
    'frequency',
    'positions',
    'waiting_time'
)

public_properties = (
    device_public_properties +
    link_public_properties
)

cls_to_properties = {
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

cls_to_properties = {k: ('id',) + v for k, v in cls_to_properties.items()}

default_diagrams_properties = {
    'device': 'model',
    'link': 'model',
    'user': 'name',
    'service': 'type',
    'workflow': 'vendor',
    'task': 'type'
}

object_diagram_properties = (
    'model',
    'vendor',
    'subtype',
    'location'
)

device_diagram_properties = object_diagram_properties + (
    'operating_system',
    'os_version'
)

user_diagram_properties = (
    'name',
)

workflow_diagram_properties = (
    'type',
    'vendor',
    'operating_system'
)

service_diagram_properties = (
    'type',
    'device_multiprocessing'
)

task_diagram_properties = (
    'type',
    'status',
    'frequency'
)

type_to_diagram_properties = {
    'device': device_diagram_properties,
    'link': object_diagram_properties,
    'user': user_diagram_properties,
    'service': service_diagram_properties,
    'workflow': workflow_diagram_properties,
    'task': task_diagram_properties
}

pretty_names = {
    'access_rights': 'Access rights',
    'action': 'Action',
    'content': 'Content',
    'content_type': 'Content type',
    'description': 'Description',
    'destination': 'Destination',
    'dest_file': 'Destination file',
    'device_multiprocessing': 'Device multiprocessing',
    'direction': 'Direction',
    'driver': 'Driver',
    'email': 'Email',
    'file': 'File',
    'file_system': 'File system',
    'frequency': 'Frequency',
    'getters': 'Getters',
    'global_delay_factor': 'Global delay factor',
    'inventory_from_selection': 'Inventory from selection',
    'ip_address': 'IP address',
    'longitude': 'Longitude',
    'latitude': 'Latitude',
    'location': 'Location',
    'model': 'Model',
    'name': 'Name',
    'operating_system': 'Operating System',
    'os_version': 'OS version',
    'pass_device_properties': 'Pass device properties to the playbook',
    'password': 'Password',
    'permission': 'Permission',
    'positions': 'Positions',
    'recurrent': 'Recurrent',
    'enable_password': 'Enable password',
    'source': 'Source',
    'source_file': 'Source file',
    'status': 'Status',
    'subtype': 'Subtype',
    'text file': 'File',
    'type': 'Type',
    'username': 'Username',
    'vendor': 'Vendor',
    'waiting_time': 'Waiting time'
}

reverse_pretty_names = {v: k for k, v in pretty_names.items()}

property_types = {
    'content_match_regex': bool,
    'content_match_regex1': bool,
    'content_match_regex2': bool,
    'content_match_regex3': bool,
    'disable_md5': bool,
    'gotty_port_redirection': bool,
    'inline_transfer': bool,
    'inventory_from_selection': bool,
    'overwrite_file': bool,
    'pass_device_properties': bool,
    'payload': dict,
    'contentregex': bool,
    'sourceregex': bool
}

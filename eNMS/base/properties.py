from collections import OrderedDict


object_common_properties = (
    'name',
    'description',
    'location',
    'type',
    'vendor'
)

node_common_properties = (
    'operating_system',
    'os_version',
    'ip_address',
    'longitude',
    'latitude',
    'secret_password'
)

link_common_properties = (
    'source',
    'destination',
)

node_public_properties = (
    object_common_properties +
    node_common_properties[:-1]
)

link_public_properties = (
    object_common_properties +
    link_common_properties
)

pool_public_properties = (
    'name',
    'description'
)

task_public_properties = (
    'name',
    'creation_time',
    'creator',
    'recurrent',
    'frequency',
    'status'
)

script_public_properties = (
    'name',
    'type',
    'description',
    'vendor',
    'operating_system',
    'waiting_time'
)

workflow_public_properties = (
    'name',
    'description',
    'type',
)

user_public_properties = (
    'name',
    'email',
    'access_rights'
)

log_public_properties = (
    'source',
    'content'
)

parameters_public_properties = (
    'default_longitude',
    'default_latitude',
    'default_zoom_level'
)

public_properties = (
    node_public_properties +
    link_public_properties
)

cls_to_properties = {
    'Node': ('id',) + node_public_properties,
    'Link': ('id', 'color') + link_public_properties,
    'Pool': ('id',) + pool_public_properties,
    'Task': ('id',) + task_public_properties,
    'Script': ('id',) + script_public_properties,
    'Parameters': parameters_public_properties,
    'Workflow': ('id',) + workflow_public_properties,
    'User': ('id',) + user_public_properties,
    'Log': ('id',) + log_public_properties
}

type_to_public_properties = OrderedDict([
    ('Antenna', node_public_properties),
    ('Firewall', node_public_properties),
    ('Host', node_public_properties),
    ('Optical switch', node_public_properties),
    ('Regenerator', node_public_properties),
    ('Router', node_public_properties),
    ('Switch', node_public_properties),
    ('Server', node_public_properties),
    ('BGP peering', link_public_properties),
    ('Etherchannel', link_public_properties),
    ('Ethernet link', link_public_properties),
    ('Optical channel', link_public_properties),
    ('Optical link', link_public_properties),
    ('Pseudowire', link_public_properties)
])

## Diagram properties (for the dashboard)

default_diagrams_properties = {
    'node': 'vendor',
    'link': 'location',
    'user': 'access_rights',
    'script': 'type',
    'workflow': 'vendor',
    'task': 'type'
}

object_diagram_properties = (
    'description',
    'location',
)

node_diagram_properties = object_diagram_properties + (
    'type',
    'vendor',
    'operating_system',
    'os_version'
)

link_diagram_properties = object_diagram_properties + (
    'type',
    'vendor'
)

user_diagram_properties = (
    'type',
    'access_rights',
)

workflow_diagram_properties = (
    'type',
    'vendor',
    'operating_system'
)

script_diagram_properties = (
    'type',
    'vendor',
    'operating_system'
)

task_diagram_properties = (
    'type',
    'recurrent',
)

type_to_diagram_properties = {
    'node': node_diagram_properties,
    'link': link_diagram_properties,
    'user': user_diagram_properties,
    'script': script_diagram_properties,
    'workflow': workflow_diagram_properties,
    'task': task_diagram_properties
}

pretty_names = OrderedDict([
    ('access_rights', 'Access rights'),
    ('action', 'Action'),
    ('content', 'Content'),
    ('content_type', 'Content type'),
    ('description', 'Description'),
    ('destination', 'Destination'),
    ('dest_file', 'Destination file'),
    ('direction', 'Direction'),
    ('driver', 'Driver'),
    ('email', 'Email'),
    ('file', 'File'),
    ('file_system', 'File system'),
    ('getters', 'Getters'),
    ('global_delay_factor', 'Global delay factor'),
    ('ip_address', 'IP address'),
    ('longitude', 'Longitude'),
    ('latitude', 'Latitude'),
    ('location', 'Location'),
    ('name', 'Name'),
    ('netmiko_type', 'Netmiko type'),
    ('operating_system', 'Operating System'),
    ('os_version', 'OS version'),
    ('recurrent', 'Recurrent'),
    ('secret_password', 'Secret password'),
    ('source', 'Source'),
    ('source_file', 'Source file'),
    ('text file', 'File'),
    ('type', 'Type'),
    ('vendor', 'Vendor'),
    ('waiting_time', 'Waiting time')
])

reverse_pretty_names = {v: k for k, v in pretty_names.items()}

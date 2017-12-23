from collections import OrderedDict

object_common_properties = OrderedDict([
    ('name', 'Name'),
    ('type', 'Type'),
    ('vendor', 'Vendor')
    ])

node_common_properties = OrderedDict([
    ('operating_system', 'Operating System'),
    ('os_version', 'OS version'),
    ('ip_address', 'IP address'),
    ('longitude', 'Longitude'),
    ('latitude', 'Latitude')
    ])

link_common_properties = OrderedDict([
    ('source', 'Source'),
    ('destination', 'Destination')
    ])

node_public_properties = (
tuple(object_common_properties) + 
tuple(node_common_properties)
)

link_public_properties = (
tuple(object_common_properties) + 
tuple(link_common_properties)
)

public_properties = (
tuple(node_public_properties) + 
tuple(link_public_properties)
)

type_to_public_properties = OrderedDict([
    ('Router', node_common_properties),
    ('Optical switch', node_common_properties),
    ('Optical link', link_common_properties)
    ])

pretty_names = OrderedDict([
    ('name', 'Name'),
    ('type', 'Type'),
    ('vendor', 'Vendor'),
    ('operating_system', 'Operating System'),
    ('os_version', 'OS version'),
    ('ip_address', 'IP address'),
    ('longitude', 'Longitude'),
    ('latitude', 'Latitude'),
    ('source', 'Source'),
    ('destination', 'Destination')
    ])
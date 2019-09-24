from typing import Dict, List

device_icons[str, str] = {
    "antenna": "Antenna",
    "firewall": "Firewall",
    "host": "Host",
    "optical_switch": "Optical switch",
    "regenerator": "Regenerator",
    "router": "Router",
    "server": "Server",
    "switch": "Switch",
}

object_common_properties[str] = [
    "name",
    "description",
    "subtype",
    "model",
    "location",
    "vendor",
]

device_properties = [
    "icon",
    "operating_system",
    "os_version",
    "netmiko_driver",
    "napalm_driver",
    "ip_address",
    "port",
    "longitude",
    "latitude",
    "username",
]

pool_device_properties[str] = (
    object_common_properties + device_properties[:-1] + ["current_configuration"]
)

link_properties[str] = object_common_properties + [
    "color",
    "source_name",
    "destination_name",
    "source",
    "destination",
]

pool_link_properties[str] = link_properties[:-2]

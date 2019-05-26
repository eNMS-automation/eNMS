from typing import Dict, List

device_icons: Dict[str, str] = {
    "antenna": "Antenna",
    "firewall": "Firewall",
    "host": "Host",
    "optical_switch": "Optical switch",
    "regenerator": "Regenerator",
    "router": "Router",
    "server": "Server",
    "switch": "Switch",
}

object_common_properties: List[str] = [
    "name",
    "description",
    "subtype",
    "icon",
    "model",
    "location",
    "vendor",
]

device_properties = [
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

pool_device_properties: List[str] = (
    object_common_properties + device_properties[:-1] + ["current_configuration"]
)

link_properties: List[str] = object_common_properties + [
    "source_name",
    "destination_name",
    "source",
    "destination",
]

pool_link_properties: List[str] = link_properties[:-2]

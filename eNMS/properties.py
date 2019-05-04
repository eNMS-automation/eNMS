from os import environ
from sqlalchemy import Boolean, Float, Integer, Text
from yaml import load, BaseLoader
from typing import Dict, List

from eNMS.database import DB_STRING_LENGTH


def get_custom_properties() -> dict:
    filepath = environ.get("PATH_CUSTOM_PROPERTIES")
    if not filepath:
        return {}
    with open(filepath, "r") as properties:
        return load(properties, Loader=BaseLoader)


sql_types: dict = {
    "boolean": Boolean,
    "float": Float,
    "integer": Integer,
    "string": Text(DB_STRING_LENGTH),
}

google_earth_styles: dict = {}

custom_properties: dict = get_custom_properties()

list_properties: List[str] = [
    "devices",
    "pools",
    "links",
    "permissions",
    "getters",
    "import_export_types",
    "deletion_types",
]

private_properties: List[str] = ["password", "enable_password"]

base_properties: List[str] = ["id", "name", "description"]

object_common_properties: List[str] = base_properties + [
    "subtype",
    "model",
    "location",
    "vendor",
]

device_subtypes: Dict[str, str] = {
    "antenna": "Antenna",
    "firewall": "Firewall",
    "host": "Host",
    "optical_switch": "Optical switch",
    "regenerator": "Regenerator",
    "router": "Router",
    "server": "Server",
    "switch": "Switch",
}

subtype_sizes: Dict[str, List] = {
    "antenna": [18, 12],
    "firewall": [18, 12],
    "host": [18, 12],
    "optical_switch": [18, 12],
    "regenerator": [18, 12],
    "router": [18, 12],
    "server": [18, 12],
    "switch": [18, 12],
    "site": [22, 22],
}

link_subtypes: Dict[str, str] = {
    "bgp_peering": "BGP peering",
    "etherchannel": "Etherchannel",
    "ethernet_link": "Ethernet link",
    "optical_channel": "Optical channel",
    "optical_link": "Optical link",
    "pseudowire": "Pseudowire",
}

link_subtype_to_color: Dict[str, str] = {
    "bgp_peering": "#77ebca",
    "etherchannel": "#cf228a",
    "ethernet_link": "#0000ff",
    "optical_link": "#d4222a",
    "optical_channel": "#ff8247",
    "pseudowire": "#902bec",
}

device_properties = list(custom_properties) + [
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

device_table_properties: List[str] = (
    object_common_properties[1:] + device_properties[:-3]
)

pool_device_properties: List[str] = (
    object_common_properties[1:] + device_properties[:-1] + ["current_configuration"]
)

device_public_properties: List[str] = object_common_properties + device_properties + [
    "last_failure",
    "last_runtime",
    "last_status",
    "last_update",
]

device_configuration_properties: List[str] = [
    "name",
    "model",
    "last_failure",
    "last_runtime",
    "last_update",
    "last_status",
]

task_properties: List[str] = base_properties + [
    "job",
    "job_name",
    "next_run_time",
    "scheduling_mode",
    "start_date",
    "end_date",
    "frequency",
    "frequency_unit",
    "crontab_expression",
    "is_active",
]

task_public_properties: List[str] = task_properties[1:]

link_properties: List[str] = object_common_properties + [
    "source_name",
    "destination_name",
    "source",
    "destination",
]

pool_link_properties: List[str] = link_properties[1:-2]

link_table_properties: List[str] = object_common_properties[1:] + [
    "source_name",
    "destination_name",
]

pool_public_properties: List[str] = base_properties + [
    "never_update",
    "longitude",
    "latitude",
    "object_number",
]

pool_table_properties: List[str] = pool_public_properties[1:]

for obj_type, properties in (
    ("device", pool_device_properties),
    ("link", pool_link_properties),
):
    for prop in properties:
        pool_public_properties.extend(
            [f"{obj_type}_{prop}", f"{obj_type}_{prop}_match"]
        )

service_table_properties: List[str] = [
    "name",
    "type",
    "description",
    "creator_name",
    "number_of_retries",
    "time_between_retries",
    "status",
    "progress",
]

workflow_table_properties: List[str] = [
    "name",
    "description",
    "creator_name",
    "vendor",
    "operating_system",
    "number_of_retries",
    "time_between_retries",
    "status",
    "progress",
]

workflow_edge_properties: List[str] = [
    "id",
    "name",
    "subtype",
    "source_id",
    "destination_id",
]

user_table_properties: List[str] = ["name", "email"]

server_table_properties = base_properties[1:] + [
    "ip_address",
    "weight",
    "status",
    "cpu_load",
]

user_permissions: List[str] = ["Admin", "Connect to device", "View", "Edit"]

log_public_properties: List[str] = ["source_ip", "content"]

log_rule_public_properties: List[str] = log_public_properties + [
    "name",
    "source_ip_regex",
    "content_regex",
    "jobs",
]

log_rule_table_properties: List[str] = ["name"] + log_public_properties

task_table_properties: List[str] = [
    "name",
    "description",
    "job_name",
    "status",
    "scheduling_mode",
    "start_date",
    "end_date",
    "frequency",
    "frequency_unit",
    "crontab_expression",
    "next_run_time",
    "time_before_next_run",
]

table_properties: Dict[str, List[str]] = {
    "configuration": device_configuration_properties,
    "device": device_table_properties,
    "server": server_table_properties,
    "link": link_table_properties,
    "log": log_public_properties,
    "logrule": log_rule_table_properties,
    "pool": pool_table_properties,
    "service": service_table_properties,
    "task": task_table_properties,
    "user": user_table_properties,
    "workflow": workflow_table_properties,
}

job_filtering_properties = {
    "name",
    "type",
    "description",
    "creator_name",
    "max_processes",
    "credentials",
    "waiting_time",
    "send_notification_method",
    "mail_recipient",
    "number_of_retries",
    "time_between_retries",
}

filtering_properties: Dict[str, List[str]] = {
    "configuration": device_configuration_properties + ["current_configuration"],
    "device": device_table_properties + ["current_configuration"],
    "server": server_table_properties,
    "link": link_table_properties,
    "log": log_public_properties,
    "logrule": log_rule_table_properties,
    "pool": pool_table_properties,
    "service": job_filtering_properties,
    "task": task_table_properties,
    "user": user_table_properties,
    "workflow": job_filtering_properties,
}

table_fixed_columns: Dict[str, List[str]] = {
    "configuration": ["Configuration", "Download", "Edit"],
    "device": ["Automation", "Connect", "Edit", "Duplicate", "Delete"],
    "server": ["Edit", "Duplicate", "Delete"],
    "link": ["Edit", "Duplicate", "Delete"],
    "log": ["Delete"],
    "logrule": ["Edit", "Delete"],
    "service": ["Logs", "Results", "Run", "Edit", "Duplicate", "Delete"],
    "task": ["Action", "Edit", "Duplicate", "Delete"],
    "user": ["Edit", "Duplicate", "Delete"],
    "pool": ["Visualize", "Edit", "Update", "Duplicate", "Edit objects", "Delete"],
    "workflow": ["Logs", "Results", "Run", "Edit", "Duplicate", "Delete"],
}

object_diagram_properties: List[str] = ["model", "vendor", "subtype", "location"]

device_diagram_properties: List[str] = (
    object_diagram_properties
    + ["operating_system", "os_version", "port"]
    + list(p for p, v in custom_properties.items() if v["add_to_dashboard"])
)

user_diagram_properties: List[str] = ["name"]

service_diagram_properties: List[str] = [
    "vendor",
    "operating_system",
    "creator_name",
    "send_notification",
    "send_notification_method",
    "multiprocessing",
    "max_processes",
    "number_of_retries",
    "time_between_retries",
]

workflow_diagram_properties: List[str] = service_diagram_properties

task_diagram_properties: List[str] = [
    "status",
    "periodic",
    "frequency",
    "frequency_unit",
    "crontab_expression",
    "job_name",
]

type_to_diagram_properties: Dict[str, List[str]] = {
    "Device": device_diagram_properties,
    "Link": object_diagram_properties,
    "User": user_diagram_properties,
    "Service": service_diagram_properties,
    "Workflow": workflow_diagram_properties,
    "Task": task_diagram_properties,
}

pretty_names: Dict[str, str] = {
    "access_rights": "Access rights",
    "action": "Action",
    "call_type": "Type of call",
    "command": "Command",
    "command1": "Command 1",
    "command2": "Command 2",
    "command3": "Command 3",
    "current_configuration": "Current Configuration",
    "content": "Content",
    "content_match": "Content Match",
    "content_match_regex": "Match content against Regular expression",
    "content_type": "Content type",
    "crontab_expression": "Crontab expression",
    "cpu_load": "CPU load",
    "creator": "Creator",
    "creator_name": "Creator",
    "delay_factor": "Delay factor",
    "delete_archive": "Delete archive",
    "delete_folder": "Delete folder",
    "delete_spaces_before_matching": "Delete spaces before matching",
    "description": "Description",
    "destination": "Destination",
    "destination_file": "Destination file",
    "destination_name": "Destination",
    "destination_path": "Destination path",
    "dest_file": "Destination file",
    "device_multiprocessing": "Device multiprocessing",
    "dict_match": "dictionary match",
    "direction": "Direction",
    "display_only_failed_nodes": "Display only failed nodes",
    "download": "Download",
    "driver": "Driver",
    "email": "Email",
    "enable_mode": 'Enter "Enable" mode',
    "enable_password": "Enable password",
    "end_date": "End date",
    "fast_cli": "Fast CLI",
    "file": "File",
    "file_system": "File system",
    "frequency": "Frequency",
    "frequency_unit": "Frequency Unit",
    "getters": "Getters",
    "global_delay_factor": "Global delay factor",
    "has_targets": "Has targets",
    "headers": "Headers",
    "inventory_from_selection": "Inventory from selection",
    "ip_address": "IP address",
    "is_active": "Is active",
    "job_name": "Service / Workflow",
    "last_failure": "Last failure",
    "last_runtime": "Last runtime",
    "last_status": "Last status",
    "last_update": "Last update",
    "longitude": "Longitude",
    "latitude": "Latitude",
    "load_known_host_keys": "Load known host keys",
    "location": "Location",
    "look_for_keys": "Look for keys",
    "max_processes": "Maximum number of processes",
    "missing_host_key_policy": "Missing Host Key Policy",
    "model": "Model",
    "multiprocessing": "Multiprocessing",
    "name": "Name",
    "napalm_driver": "Napalm driver",
    "negative_logic": "Negative Logic",
    "netmiko_driver": "Netmiko driver",
    "never_update": "Never update",
    "next_run_time": "Next runtime",
    "number_of_configuration": "Maximum number of configurations stored in database",
    "number_of_retries": "Number of retries",
    "object_number": "Number of objects",
    "operating_system": "Operating System",
    "optional_args": "Optional arguments",
    "os_version": "OS version",
    "params": "Parameters",
    "pass_device_properties": "Pass device properties to the playbook",
    "password": "Password",
    "payload": "Payload",
    "periodic": "Periodic",
    "permission": "Permission",
    "port": "Port",
    "positions": "Positions",
    "protocol": "Protocol",
    "recurrent": "Recurrent",
    "regular_expression1": "Regular Expression 1",
    "regular_expression2": "Regular Expression 2",
    "regular_expression3": "Regular Expression 3",
    "scheduling_mode": "Scheduling Mode",
    "send_notification": "Send a notification",
    "send_notification_method": "Notification method",
    "source": "Source",
    "source_name": "Source",
    "source_file": "Source file",
    "source_ip": "Source IP address",
    "start_date": "Start date",
    "status": "Status",
    "subtype": "Subtype",
    "text file": "File",
    "time_before_next_run": "Time before next run",
    "time_between_retries": "Time between retries",
    "timeout": "Timeout (in seconds)",
    "type": "Type",
    "update_dictionary": "Update dictionary",
    "url": "URL",
    "use_device_driver": "Use driver from device",
    "username": "Username",
    "validation_method": "Validation Method",
    "variable1": "Variable 1",
    "variable2": "Variable 2",
    "variable3": "Variable 3",
    "vendor": "Vendor",
    "waiting_time": "Waiting time",
    "weight": "Weight",
}

# Import properties

pretty_names.update({k: v["pretty_name"] for k, v in custom_properties.items()})
reverse_pretty_names: Dict[str, str] = {v: k for k, v in pretty_names.items()}

relationships: Dict[str, Dict[str, str]] = {
    "User": {"pool": "Pool"},
    "Device": {"job": "Job"},
    "Link": {"source": "Device", "destination": "Device"},
    "Pool": {"device": "Device", "link": "Link"},
    "Service": {
        "creator": "User",
        "device": "Device",
        "pool": "Pool",
        "workflow": "Workflow",
        "task": "Task",
    },
    "Task": {"job": "Job"},
    "Workflow": {
        "creator": "User",
        "edge": "WorkflowEdge",
        "job": "Job",
        "device": "Device",
        "pool": "Pool",
    },
    "WorkflowEdge": {"source": "Job", "destination": "Job", "workflow": "Workflow"},
    "LogRule": {"job": "Job", "log": "Log"},
}


import_classes = [
    "User",
    "Device",
    "Link",
    "Pool",
    "Service",
    "Workflow",
    "WorkflowEdge",
    "Task",
]

# Export topology properties

export_properties: Dict[str, List[str]] = {
    "Device": device_public_properties,
    "Link": link_table_properties,
}

# Properties that shouldn't be in the migration files

dont_migrate: Dict[str, List[str]] = {
    "Device": ["jobs"],
    "Pool": ["object_number"],
    "Service": [
        "results",
        "logs",
        "state",
        "tasks",
        "is_running",
        "status",
        "workflows",
        "creator_name",
    ],
    "Task": [
        "job_name",
        "next_run_time",
        "is_active",
        "time_before_next_run",
        "status",
    ],
    "Workflow": [
        "last_modified",
        "results",
        "logs",
        "state",
        "status",
        "is_running",
        "creator_name",
    ],
}

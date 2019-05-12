from typing import Dict, List

from eNMS import controller

private_properties: List[str] = ["password", "enable_password"]

base_properties: List[str] = ["id", "name", "description"]

object_common_properties: List[str] = base_properties + [
    "subtype",
    "model",
    "location",
    "vendor",
]

device_properties = list(controller.custom_properties) + [
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

device_configuration_properties: List[str] = [
    "name",
    "model",
    "last_failure",
    "last_runtime",
    "last_update",
    "last_status",
]

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

pool_table_properties: List[str] = base_properties[1:] + [
    "never_update",
    "longitude",
    "latitude",
    "object_number",
]

service_table_properties: List[str] = [
    "name",
    "type",
    "description",
    "creator",
    "number_of_retries",
    "time_between_retries",
    "status",
    "progress",
]

workflow_table_properties: List[str] = [
    "name",
    "description",
    "creator",
    "vendor",
    "operating_system",
    "number_of_retries",
    "time_between_retries",
    "status",
    "progress",
]

user_table_properties: List[str] = ["name", "email"]

server_table_properties = base_properties[1:] + [
    "ip_address",
    "weight",
    "status",
    "cpu_load",
]

user_permissions: List[str] = ["Admin", "Connect to device", "View", "Edit"]

log_public_properties: List[str] = ["time", "origin", "severity", "name"]

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
    "creator",
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
    "log": [],
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
    + list(p for p, v in controller.custom_properties.items() if v["add_to_dashboard"])
)

user_diagram_properties: List[str] = ["name"]

service_diagram_properties: List[str] = [
    "vendor",
    "operating_system",
    "creator",
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

property_names: Dict[str, str] = {
    k: v["property_name"] for k, v in controller.custom_properties.items()
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

# Properties that shouldn't be in the migration files

dont_migrate: Dict[str, List[str]] = {
    "Device": ["jobs", "source", "destination", "pools"],
    "Link": ["pools"],
    "Pool": ["object_number"],
    "Service": [
        "sources",
        "destinations",
        "results",
        "logs",
        "state",
        "tasks",
        "is_running",
        "status",
        "workflows",
        "tasks",
    ],
    "Task": [
        "job_name",
        "next_run_time",
        "is_active",
        "time_before_next_run",
        "status",
    ],
    "Workflow": [
        "sources",
        "destinations",
        "last_modified",
        "results",
        "logs",
        "state",
        "status",
        "is_running",
        "workflows",
        "tasks",
    ],
}

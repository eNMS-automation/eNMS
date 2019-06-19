from typing import Dict, List

from eNMS.properties.objects import object_common_properties

device_table_properties: List[str] = object_common_properties + [
    "operating_system",
    "os_version",
    "ip_address",
    "port",
]

configuration_table_properties: List[str] = [
    "name",
    "model",
    "last_failure",
    "last_runtime",
    "last_update",
    "last_status",
]

link_table_properties: List[str] = object_common_properties + [
    "source_name",
    "destination_name",
]

pool_table_properties: List[str] = [
    "name",
    "last_modified",
    "description",
    "never_update",
    "longitude",
    "latitude",
    "object_number",
]

service_table_properties: List[str] = [
    "name",
    "last_modified",
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
    "last_modified",
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

server_table_properties = [
    "name",
    "description",
    "ip_address",
    "weight",
    "status",
    "cpu_load",
]

log_table_properties: List[str] = ["time", "origin", "severity", "content"]

event_table_properties: List[str] = ["name"] + log_table_properties

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
    "configuration": configuration_table_properties,
    "device": device_table_properties,
    "server": server_table_properties,
    "link": link_table_properties,
    "log": log_table_properties,
    "event": event_table_properties,
    "pool": pool_table_properties,
    "service": service_table_properties,
    "task": task_table_properties,
    "user": user_table_properties,
    "workflow": workflow_table_properties,
}

job_filtering_properties = [
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
]

filtering_properties: Dict[str, List[str]] = {
    "configuration": device_table_properties
    + configuration_table_properties
    + ["current_configuration"],
    "device": device_table_properties + ["current_configuration"],
    "server": server_table_properties,
    "link": link_table_properties,
    "log": log_table_properties,
    "event": event_table_properties,
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
    "event": ["Edit", "Delete"],
    "service": ["Logs", "Results", "Run", "Edit", "Duplicate", "Export", "Delete"],
    "task": ["Action", "Edit", "Duplicate", "Delete"],
    "user": ["Edit", "Duplicate", "Delete"],
    "pool": ["Visualize", "Edit", "Update", "Duplicate", "Edit objects", "Delete"],
    "workflow": ["Logs", "Results", "Run", "Edit", "Duplicate", "Export", "Delete"],
}

from typing import Dict, List

from eNMS.properties.objects import (
    device_properties as device_class_properties,
    object_common_properties,
)

device_properties: List[str] = object_common_properties + device_properties[:-3]

configuration_properties: List[str] = [
    "name",
    "model",
    "last_failure",
    "last_runtime",
    "last_update",
    "last_status",
]

link_properties: List[str] = object_common_properties[1:] + [
    "source_name",
    "destination_name",
]

pool_properties: List[str] = [
    "name",
    "description",
    "never_update",
    "longitude",
    "latitude",
    "object_number",
]

service_properties: List[str] = [
    "name",
    "type",
    "description",
    "creator",
    "number_of_retries",
    "time_between_retries",
    "status",
    "progress",
]

workflow_properties: List[str] = [
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

user_properties: List[str] = ["name", "email"]

server_properties = [
    "name",
    "description",
    "ip_address",
    "weight",
    "status",
    "cpu_load",
]

log_properties: List[str] = ["time", "origin", "severity", "content"]

log_rule_properties: List[str] = ["name"] + log_properties

task_properties: List[str] = [
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
    "configuration": configuration_properties,
    "device": device_properties,
    "server": server_properties,
    "link": link_properties,
    "log": log_properties,
    "logrule": log_rule_properties,
    "pool": pool_properties,
    "service": service_properties,
    "task": task_properties,
    "user": user_properties,
    "workflow": workflow_properties,
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
    "configuration": configuration_properties + ["current_configuration"],
    "device": device_properties + ["current_configuration"],
    "server": server_properties,
    "link": link_properties,
    "log": log_properties,
    "logrule": log_rule_properties,
    "pool": pool_properties,
    "service": job_filtering_properties,
    "task": task_properties,
    "user": user_properties,
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

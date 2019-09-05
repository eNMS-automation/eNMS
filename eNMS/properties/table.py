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
    "vendor",
    "operating_system",
    "creator",
]

workflow_table_properties: List[str] = [
    "name",
    "last_modified",
    "description",
    "vendor",
    "operating_system",
    "creator",
    "vendor",
    "operating_system",
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

syslog_table_properties: List[str] = ["time", "source", "content"]

changelog_table_properties: List[str] = ["time", "user", "severity", "content"]

event_table_properties: List[str] = ["name", "log_source", "log_content"]

run_table_properties: List[str] = [
    "runtime",
    "endtime",
    "job_name",
    "workflow_name",
    "status",
    "progress",
]

result_table_properties: List[str] = [
    "runtime",
    "endtime",
    "job_name",
    "device_name",
    "workflow_name",
    "success",
]

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
    "changelog": changelog_table_properties,
    "configuration": configuration_table_properties,
    "device": device_table_properties,
    "event": event_table_properties,
    "link": link_table_properties,
    "pool": pool_table_properties,
    "result": result_table_properties,
    "run": run_table_properties,
    "server": server_table_properties,
    "service": service_table_properties,
    "syslog": syslog_table_properties,
    "task": task_table_properties,
    "user": user_table_properties,
    "workflow": workflow_table_properties,
}

job_filtering_properties = [
    "name",
    "last_modified",
    "type",
    "description",
    "vendor",
    "operating_system",
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
    "changelog": changelog_table_properties,
    "configuration": device_table_properties
    + configuration_table_properties[2:]
    + ["current_configuration"],
    "device": device_table_properties + ["current_configuration"],
    "event": event_table_properties,
    "link": link_table_properties,
    "pool": pool_table_properties,
    "result": result_table_properties,
    "run": run_table_properties[:-1],
    "server": server_table_properties,
    "service": job_filtering_properties,
    "syslog": syslog_table_properties,
    "task": task_table_properties[:-2],
    "user": user_table_properties,
    "workflow": job_filtering_properties,
}

table_fixed_columns: Dict[str, List[str]] = {
    "changelog": [],
    "configuration": ["Configuration", "Download", "Edit"],
    "device": ["Automation", "Connect", "Edit", "Duplicate", "Delete"],
    "event": ["Edit", "Delete"],
    "link": ["Edit", "Duplicate", "Delete"],
    "run": ["Logs", "Results"],
    "result": ["Result"],
    "server": ["Edit", "Duplicate", "Delete"],
    "service": [
        "Status",
        "Results",
        "Run",
        "Edit",
        "Delete",
    ],
    "syslog": [],
    "task": ["Action", "Edit", "Duplicate", "Delete"],
    "user": ["Edit", "Duplicate", "Delete"],
    "pool": ["Visualize", "Edit", "Update", "Duplicate", "Edit objects", "Delete"],
    "workflow": [
        "Status",
        "Logs",
        "Results",
        "Run",
        "Run with Updates",
        "Edit",
        "Duplicate",
        "Export",
        "Delete",
    ],
}

from eNMS.properties.objects import object_common_properties

device_table_properties = object_common_properties + [
    "operating_system",
    "os_version",
    "ip_address",
    "port",
]

link_table_properties = object_common_properties + ["source_name", "destination_name"]

pool_table_properties = [
    "name",
    "last_modified",
    "description",
    "never_update",
    "longitude",
    "latitude",
    "object_number",
]

service_table_properties = [
    "name",
    "last_modified",
    "type",
    "description",
    "vendor",
    "operating_system",
    "creator",
]

user_table_properties = ["name", "email"]

server_table_properties = [
    "name",
    "description",
    "ip_address",
    "weight",
    "status",
    "cpu_load",
]

changelog_table_properties = ["time", "user", "severity", "content"]

event_table_properties = ["name", "log_source", "log_content"]

run_table_properties = [
    "runtime",
    "endtime",
    "service_name",
    "workflow_name",
    "status",
    "progress",
]

result_table_properties = [
    "runtime",
    "endtime",
    "workflow_name",
    "service_name",
    "parent_device_name",
    "device_name",
    "success",
]

task_table_properties = [
    "name",
    "description",
    "service_name",
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

table_properties = {
    "changelog": changelog_table_properties,
    "device": device_table_properties,
    "event": event_table_properties,
    "link": link_table_properties,
    "pool": pool_table_properties,
    "result": result_table_properties,
    "run": run_table_properties,
    "server": server_table_properties,
    "service": service_table_properties,
    "task": task_table_properties,
    "user": user_table_properties,
}

service_filtering_properties = [
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

filtering_properties = {
    "changelog": changelog_table_properties,
    "device": device_table_properties + ["configuration", "operational_data"],
    "event": event_table_properties,
    "link": link_table_properties,
    "pool": pool_table_properties,
    "result": result_table_properties,
    "run": run_table_properties[:-1],
    "server": server_table_properties,
    "service": service_filtering_properties,
    "task": task_table_properties[:-2],
    "user": user_table_properties,
}

table_fixed_columns = {
    "changelog": [],
    "device": [""],
    "event": [""],
    "link": [""],
    "run": [""],
    "result": ["Result", "V1", "V2"],
    "server": [""],
    "service": ["Status", ""],
    "task": [""],
    "user": [""],
    "pool": [""],
}

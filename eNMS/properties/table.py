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

event_table_properties = ["name", "service_name", "log_source", "log_content"]

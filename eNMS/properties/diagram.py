from typing import Dict, List

from eNMS import controller

diagram_classes = ["Device", "Link", "User", "Service", "Workflow", "Task"]

object_properties: List[str] = ["model", "vendor", "subtype", "location"]

device_properties: List[str] = object_properties + [
    "operating_system",
    "os_version",
    "port",
]

user_properties: List[str] = ["name"]

service_properties: List[str] = [
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

workflow_properties: List[str] = service_properties

task_properties: List[str] = [
    "status",
    "periodic",
    "frequency",
    "frequency_unit",
    "crontab_expression",
    "job_name",
]

type_to_diagram_properties: Dict[str, List[str]] = {
    "Device": device_properties,
    "Link": object_properties,
    "User": user_properties,
    "Service": service_properties,
    "Workflow": workflow_properties,
    "Task": task_properties,
}

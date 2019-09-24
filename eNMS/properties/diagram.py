diagram_classes = ["device", "link", "user", "service", "workflow", "task"]

object_diagram_properties = ["model", "vendor", "subtype", "icon", "location"]

device_diagram_properties = object_diagram_properties + [
    "operating_system",
    "os_version",
    "port",
]

user_diagram_properties = ["name"]

service_diagram_properties = [
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

workflow_diagram_properties = service_diagram_properties

task_diagram_properties = [
    "status",
    "periodic",
    "frequency",
    "frequency_unit",
    "crontab_expression",
    "job_name",
]

type_to_diagram_properties = {
    "device": device_diagram_properties,
    "workflow": workflow_diagram_properties,
    "link": object_diagram_properties,
    "service": service_diagram_properties,
    "user": user_diagram_properties,
    "task": task_diagram_properties,
}

from ast import literal_eval
from json import loads


def dict_conversion(input):
    try:
        return literal_eval(input)
    except Exception:
        return loads(input)


field_conversion = {
    "dict": dict_conversion,
    "float": float,
    "int": int,
    "integer": int,
    "json": loads,
    "list": str,
    "str": str,
    "date": str,
}

property_names = {}

private_properties = [
    "password",
    "enable_password",
    "custom_password",
    "netbox_token",
    "librenms_token",
    "opennms_password",
]

dont_serialize = {"device": ["configuration", "operational_data"]}


import_classes = ["user", "device", "link", "pool", "service", "workflow_edge", "task"]


dont_migrate = {
    "device": [
        "id",
        "configuration",
        "operational_data",
        "services",
        "source",
        "destination",
        "pools",
    ],
    "link": ["id", "pools"],
    "pool": ["id", "services"],
    "service": [
        "id",
        "sources",
        "destinations",
        "status",
        "tasks",
        "workflows",
        "tasks",
        "edges",
    ],
    "task": [
        "id",
        "service_name",
        "next_run_time",
        "is_active",
        "time_before_next_run",
        "status",
    ],
    "user": ["id", "pools"],
    "workflow_edge": ["id", "source_id", "destination_id", "workflow_id"],
}

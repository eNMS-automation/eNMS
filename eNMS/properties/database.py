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

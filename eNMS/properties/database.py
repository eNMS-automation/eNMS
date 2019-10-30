import_classes = ["user", "device", "link", "pool", "service", "workflow_edge", "task"]

dont_track_changes = [
    "configuration",
    "current_device",
    "current_service",
    "labels",
    "last_modified",
    "operational_data",
    "positions",
    "state",
]

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
    "pool": ["id", "services", "object_number"],
    "service": [
        "id",
        "sources",
        "destinations",
        "tasks",
        "workflows",
        "tasks",
        "edges",
        "start_workflows",
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

from typing import Dict, List

import_classes = [
    "User",
    "Device",
    "Link",
    "Pool",
    "Service",
    "Workflow",
    "WorkflowEdge",
    "Task",
]

private_properties: List[str] = ["password", "enable_password"]

dont_track_changes = [
    "completed",
    "configurations",
    "current_configuration",
    "current_device",
    "current_job",
    "failed",
    "last_modified",
    "logs",
    "positions",
    "results",
    "state",
]

dont_migrate: Dict[str, List[str]] = {
    "Device": ["jobs", "source", "destination", "pools"],
    "Link": ["pools"],
    "Pool": ["last_modified", "object_number"],
    "Service": [
        "sources",
        "destinations",
        "results",
        "last_modified",
        "logs",
        "state",
        "tasks",
        "is_running",
        "status",
        "workflows",
        "tasks",
    ],
    "Task": [
        "job_name",
        "next_run_time",
        "is_active",
        "time_before_next_run",
        "status",
    ],
    "Workflow": [
        "sources",
        "destinations",
        "last_modified",
        "results",
        "logs",
        "state",
        "status",
        "is_running",
        "workflows",
        "tasks",
    ],
}

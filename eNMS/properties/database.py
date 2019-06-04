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
    "Device": ["id", "jobs", "source", "destination", "pools"],
    "Link": ["id", "pools"],
    "Pool": ["id", "last_modified", "object_number"],
    "Service": [
        "id",
        "sources",
        "destinations",
        "results",
        "logs",
        "state",
        "tasks",
        "is_running",
        "status",
        "workflows",
        "tasks",
    ],
    "Task": [
        "id",
        "job_name",
        "next_run_time",
        "is_active",
        "time_before_next_run",
        "status",
    ],
    "Workflow": [
        "edges",
        "id",
        "sources",
        "destinations",
        "results",
        "logs",
        "state",
        "status",
        "is_running",
        "workflows",
        "tasks",
    ],
    "WorkflowEdge": ["id", "source_id", "destination_id", "workflow_id"],
}

from typing import Dict, List

import_classes = [
    "User",
    "Device",
    "Link",
    "Pool",
    "Service",
    "workflow",
    "WorkflowEdge",
    "Task",
]

dont_track_changes = [
    "configurations",
    "current_configuration",
    "current_device",
    "current_job",
    "last_modified",
    "positions",
    "state",
]

dont_migrate: Dict[str, List[str]] = {
    "Device": [
        "id",
        "configurations",
        "current_configuration",
        "jobs",
        "source",
        "destination",
        "pools",
    ],
    "Link": ["id", "pools"],
    "Pool": ["id", "jobs", "object_number"],
    "Service": [
        "id",
        "sources",
        "destinations",
        "tasks",
        "workflows",
        "tasks",
        "start_workflows",
    ],
    "Task": [
        "id",
        "job_name",
        "next_run_time",
        "is_active",
        "time_before_next_run",
        "status",
    ],
    "User": ["id", "pools"],
    "workflow": ["edges", "id", "sources", "destinations", "workflows", "tasks"],
    "WorkflowEdge": ["id", "source_id", "destination_id", "workflow_id"],
}

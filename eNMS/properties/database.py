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
    "Pool": ["id", "jobs", "last_modified", "object_number"],
    "Service": [
        "id",
        "sources",
        "destinations",
        "state",
        "tasks",
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
        "state",
        "status",
        "workflows",
        "tasks",
    ],
    "WorkflowEdge": ["id", "source_id", "destination_id", "workflow_id"],
}

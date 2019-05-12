from typing import Dict, List

private_properties: List[str] = ["password", "enable_password"]

dont_track_changes = ["positions"]

dont_migrate: Dict[str, List[str]] = {
    "Device": ["jobs", "source", "destination", "pools"],
    "Link": ["pools"],
    "Pool": ["object_number"],
    "Service": [
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

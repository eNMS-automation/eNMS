from typing import Optional, Set

from eNMS.database import fetch
from eNMS.modules import scheduler


def threaded_job(
    job_id: int,
    aps_job_id: Optional[str] = None,
    targets: Optional[Set["Device"]] = None,
    payload: Optional[dict] = None,
) -> None:
    with scheduler.app.app_context():
        task = fetch("Task", creation_time=aps_job_id)
        job = fetch("Job", id=job_id)
        if targets:
            targets = {fetch("Device", id=device_id) for device_id in targets}
        job.try_run(targets=targets, payload=payload, task=task)

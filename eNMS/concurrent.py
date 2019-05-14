from multiprocessing import Lock
from typing import List, Optional, Set, Tuple

from eNMS.database.functions import fetch, session_scope


def threaded_job(
    job_id: int,
    aps_job_id: Optional[str] = None,
    targets: Optional[Set["Device"]] = None,
    payload: Optional[dict] = None,
) -> None:
    with session_scope() as session:
        task = fetch("Task", creation_time=aps_job_id)
        job = fetch("Job", id=job_id)
        if targets:
            targets = {fetch("Device", id=device_id) for device_id in targets}
        job.try_run(session, targets=targets, payload=payload, task=task)


def device_process(
    args: Tuple[int, int, Lock, dict, list, List[str], dict, Optional[int]]
) -> None:
    device_id, service_id, lock, results, logs, payload, workflow_id = args
    device = fetch("Device", id=device_id)
    workflow = fetch("Workflow", id=workflow_id)
    service = fetch("Service", id=service_id)
    device_result, device_log = service.get_results(payload, device, workflow)
    with lock:
        results["devices"][device.name] = device_result
        logs.extend(device_log)

from typing import Optional

from eNMS.database.functions import fetch


def threaded_job(
    job_id: int,
    aps_job_id: Optional[str] = None,
    targets: Optional[set] = None,
    payload: Optional[dict] = None,
) -> None:
    task = fetch("Task", allow_none=True, creation_time=aps_job_id)
    job = fetch("Job", id=job_id)
    if targets:
        targets = {fetch("Device", id=device_id) for device_id in targets}
    job.run(targets=targets, payload=payload, task=task)


def device_process(args: tuple) -> None:
    device_id, job_id, lock, results, logs, payload, workflow_id = args
    device = fetch("Device", id=device_id)
    workflow = fetch("Workflow", allow_none=True, id=workflow_id)
    job = fetch("Job", id=job_id)
    device_result, device_log = job.get_results(payload, device, workflow)
    with lock:
        results["devices"][device.name] = device_result
        logs.extend(device_log)

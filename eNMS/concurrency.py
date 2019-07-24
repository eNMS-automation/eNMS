from typing import List, Optional

from eNMS.database.functions import fetch


def threaded_job(
    job_id: int,
    aps_job_id: Optional[str] = None,
    targets: Optional[set] = None,
    payload: Optional[dict] = None,
    start_points: Optional[List[int]] = None,
    runtime: Optional[str] = None,
) -> None:
    task = fetch("Task", allow_none=True, creation_time=aps_job_id or "")
    job = fetch("Job", id=job_id)
    if start_points:
        start_points = [fetch("Job", id=id) for id in start_points]
    payload = payload or job.initial_payload
    if targets:
        targets = {fetch("Device", id=device_id) for device_id in targets}
    job.run(
        targets=targets,
        payload=payload,
        task=task,
        start_points=start_points,
        runtime=runtime,
    )


def device_thread(args: tuple) -> None:
    device = fetch("Device", id=args[0])
    workflow = fetch("Workflow", allow_none=True, id=args[6])
    job = fetch("Job", id=args[1])
    device_result = job.get_results(args[4], args[5], device, workflow, args[7])
    with args[2]:
        args[3][device.name] = device_result

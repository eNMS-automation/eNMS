from typing import List, Optional

from eNMS.database import Session
from eNMS.database.functions import factory, fetch


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
    run_args = {
        "job": job.id,
        "payload": payload,
        "runtime": runtime,
    }
    if targets:
        run_args["targets"] = targets
    if task:
        run_args["task"] = task
    run = factory("Run", **run_args)
    run.run()


def device_thread(args: tuple) -> None:
    device = fetch("Device", id=args[0])
    run = fetch("Run", timestamp=args[1])
    device_result = run.get_results(device)
    with args[2]:
        args[3][device.name] = device_result

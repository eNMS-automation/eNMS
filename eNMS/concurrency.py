from typing import List, Optional

from eNMS.database import Session
from eNMS.database.functions import factory, fetch


def run_job(runtime, job_id, **properties) -> None:
    run = factory("Run", **{"runtime": runtime, "job": job_id})
    run.properties = properties
    run.run(payload)


def get_device_result(args: tuple) -> None:
    device = fetch("Device", id=args[0])
    run = fetch("Run", runtime=args[1])
    device_result = run.get_results(args[2], device)
    with args[3]:
        args[4][device.name] = device_result

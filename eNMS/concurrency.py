from typing import Any

from eNMS.database.functions import factory, fetch


def run_job(job_id: int, runtime: str, **properties: Any) -> dict:
    run = factory("Run", job=job_id, runtime=runtime)
    run.properties = properties
    return run.run(properties.get("payload"))


def get_device_result(args: tuple) -> None:
    device = fetch("Device", id=args[0])
    run = fetch("Run", runtime=args[1])
    device_result = run.get_results(args[2], device)
    with args[3]:
        args[4][device.name] = device_result

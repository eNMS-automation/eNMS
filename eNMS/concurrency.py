from typing import Any

from eNMS.database.functions import factory, fetch


def run_job(job: int, **kwargs: Any) -> dict:
    run_kwargs = {
        key: kwargs.pop(key) for key in ("runtime", "task") if kwargs.get(key)
    }
    run = factory("Run", job=job, **run_kwargs)
    run.properties = kwargs
    return run.run(kwargs.get("payload"))


def get_device_result(args: tuple) -> None:
    device = fetch("Device", id=args[0])
    run = fetch("Run", runtime=args[1])
    device_result = run.get_results(args[2], device)
    with args[3]:
        args[4][device.name] = device_result

from typing import Any, Optional, Set, Tuple

from eNMS.controller import controller
from eNMS.database import fetch
from eNMS.modules import db


def threaded_job(
    job_id: int,
    aps_job_id: Optional[str] = None,
    targets: Optional[Set["Device"]] = None,
    payload: Optional[dict] = None,
) -> None:
    with controller.app.app_context():
        task = fetch("Task", creation_time=aps_job_id)
        job = fetch("Job", id=job_id)
        if targets:
            targets = {fetch("Device", id=device_id) for device_id in targets}
        job.try_run(targets=targets, payload=payload, task=task)
        db.session.commit()


def device_process(
    args: Tuple["Device", dict, dict, Optional["Workflow"], Any]
) -> None:
    with controller.app.app_context():
        with controller.session_scope() as session:
            device, service, lock, results, logs, payload, workflow = args
            device = fetch("Device", id=device)
            workflow = fetch("Workflow", id=workflow)
            service = fetch("Service", id=service)
            device_result, log = service.get_results(payload, device, workflow)
            with lock:
                logs.extend(log)
                all_results = results["devices"]
                all_results[device.name] = device_result
                results["devices"] = all_results
                setattr(workflow or service, "logs", list(logs))
                session.merge(workflow or service)

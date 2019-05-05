from typing import Optional, Set

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
    self, args: Tuple[Device, dict, dict, Optional["Workflow"], Any]
) -> None:
    with controller.app.app_context():
        device, service, results, payload, workflow = args
        device = fetch("Device", id=device)
        workflow = fetch("Workflow", id=workflow)
        service = fetch("Service", id=service)
        device_result = service.get_results(payload, device, workflow, True)
        all_results = results["devices"]
        all_results[device.name] = device_result
        results["devices"] = all_results
        with lock:
            with controller.session_scope() as session:
                session.merge(workflow or service)

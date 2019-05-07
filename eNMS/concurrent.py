from multiprocessing import Lock
from typing import Any, List, Optional, Set, Tuple

from eNMS.controller import controller
from eNMS.database import fetch, session_scope
from eNMS.models.inventory import Device


def threaded_job(
    job_id: int,
    aps_job_id: Optional[str] = None,
    targets: Optional[Set[Device]] = None,
    payload: Optional[dict] = None,
) -> None:
    with controller.app.app_context():
        with session_scope() as session:
            task = fetch("Task", creation_time=aps_job_id)
            job = fetch("Job", id=job_id)
            if targets:
                targets = {fetch("Device", id=device_id) for device_id in targets}
            job.try_run(targets=targets, payload=payload, task=task)
            session.commit()


def device_process(
    args: Tuple[int, int, Lock, dict, List[str], dict, Optional[int]]
) -> None:
    with controller.app.app_context():
        with session_scope() as session:
            device_id, service_id, lock, results, logs, payload, workflow_id = args
            device = fetch("Device", id=device_id)
            workflow = fetch("Workflow", id=workflow_id)
            service = fetch("Service", id=service_id)
            device_result, log = service.get_results(payload, device, workflow)
            with lock:
                logs.extend(log)
                all_results = results["devices"]
                all_results[device.name] = device_result
                results["devices"] = all_results
                setattr(workflow or service, "logs", list(logs))
                session.merge(workflow or service)

from napalm._SUPPORTED_DRIVERS import SUPPORTED_DRIVERS
from netmiko.ssh_dispatcher import CLASS_MAPPER, FILE_TRANSFER_MAP

from eNMS.main import db, scheduler
from eNMS.base.helpers import fetch

NETMIKO_DRIVERS = sorted((driver, driver) for driver in CLASS_MAPPER)
NETMIKO_SCP_DRIVERS = sorted((driver, driver) for driver in FILE_TRANSFER_MAP)
NAPALM_DRIVERS = sorted((driver, driver) for driver in SUPPORTED_DRIVERS[1:])


def scheduler_job(job_id, aps_job_id=None, targets=None):
    with scheduler.app.app_context():
        job = fetch('Job', id=job_id)
        if targets:
            targets = [
                fetch('Device', id=device_id)
                for device_id in targets
            ]
        job.try_run(targets=targets)
        task = fetch('Task', creation_time=aps_job_id)
        if task and not task.frequency:
            task.status = 'Completed'
        db.session.commit()

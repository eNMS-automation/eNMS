from napalm import get_network_driver
from napalm._SUPPORTED_DRIVERS import SUPPORTED_DRIVERS
from netmiko import ConnectHandler
from netmiko.ssh_dispatcher import CLASS_MAPPER, FILE_TRANSFER_MAP
from re import compile

from eNMS.main import db, scheduler
from eNMS.base.helpers import fetch

NETMIKO_DRIVERS = sorted((driver, driver) for driver in CLASS_MAPPER)
NETMIKO_SCP_DRIVERS = sorted((driver, driver) for driver in FILE_TRANSFER_MAP)
NAPALM_DRIVERS = sorted((driver, driver) for driver in SUPPORTED_DRIVERS[1:])


def get_credentials(service, device):
    return (
        (service.creator.name, service.creator.password)
        if service.credentials == 'user'
        else (device.username, device.password)
    )


def netmiko_connection(service, device):
    username, password = get_credentials(service, device)
    driver = device.netmiko_driver if use_device_driver else service.driver
    return ConnectHandler(
        device_type=service.driver,
        ip=device.ip_address,
        username=username,
        password=password,
        secret=device.enable_password,
        fast_cli=service.fast_cli,
        timeout=service.timeout,
        global_delay_factor=service.global_delay_factor
    )


def napalm_connection(service, device):
    username, password = get_credentials(service, device)
    optional_args = service.optional_args
    if not optional_args:
        optional_args = {}
    if 'secret' not in optional_args:
        optional_args['secret'] = device.enable_password
    driver = get_network_driver(service.driver)
    return driver(
        hostname=device.ip_address,
        username=username,
        password=password,
        optional_args=optional_args
    )


def substitute(data, variables):
    r = compile('{{(.*?)}}')

    def replace_with_locals(match):
        return str(eval(match.group()[2:-2], variables))
    return r.sub(replace_with_locals, data)


def space_deleter(input):
    return ''.join(input.split())


def is_subdict(source, sub):
    for k, v in source.items():
        if isinstance(v, dict):
            is_subdict(v, sub)
        elif k in sub and sub[k] == v:
            sub.pop(k)
    return not sub


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

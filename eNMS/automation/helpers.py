from napalm import get_network_driver
from napalm._SUPPORTED_DRIVERS import SUPPORTED_DRIVERS
from netmiko import ConnectHandler
from netmiko.ssh_dispatcher import CLASS_MAPPER, FILE_TRANSFER_MAP
from re import compile

from eNMS import db, scheduler
from eNMS.automation.models import Job
from eNMS.base.helpers import get_device_credentials, retrieve

NETMIKO_DRIVERS = sorted(
    (driver, driver) for driver in CLASS_MAPPER
    if 'telnet' not in driver and 'ssh' not in driver
)

NETMIKO_SCP_DRIVERS = sorted((driver, driver) for driver in FILE_TRANSFER_MAP)

# we exclude "base" from supported drivers
NAPALM_DRIVERS = sorted((driver, driver) for driver in SUPPORTED_DRIVERS[1:])


def netmiko_connection(service, device):
    username, pwd, enable_pwd = get_device_credentials(scheduler.app, device)
    return ConnectHandler(
        device_type=service.driver,
        ip=device.ip_address,
        username=username,
        password=pwd,
        secret=enable_pwd,
        fast_cli=service.fast_cli
    )


def napalm_connection(service, device):
    optional_args = service.optional_args
    if not optional_args:
        optional_args = {}
    username, pwd, enable_pwd = get_device_credentials(scheduler.app, device)
    if 'secret' not in optional_args:
        optional_args['secret'] = enable_pwd
    driver = get_network_driver(service.driver)
    return driver(
        hostname=device.ip_address,
        username=username,
        password=pwd,
        optional_args=optional_args
    )


def substitute(data, variables):
    r = compile('{{(.*?)}}')

    def replace_with_locals(match):
        return str(eval(match.group()[2:-2], variables))
    return r.sub(replace_with_locals, data)


def scheduler_job(job_id):
    with scheduler.app.app_context():
        job = retrieve(Job, id=job_id)
        job.status = {'state': 'Running'}
        db.session.commit()
        job.try_run()
        job.status['state'] = 'Idle'
        db.session.commit()

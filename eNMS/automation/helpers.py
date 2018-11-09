from logging import info
from napalm import get_network_driver
from napalm._SUPPORTED_DRIVERS import SUPPORTED_DRIVERS
from netmiko import ConnectHandler
from netmiko.ssh_dispatcher import CLASS_MAPPER, FILE_TRANSFER_MAP
from os import environ
from re import compile

from eNMS import db, scheduler
from eNMS.base.helpers import fetch
from eNMS.base.security import get_device_credentials

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
        fast_cli=service.fast_cli,
        timeout=service.timeout,
        global_delay_factor=service.global_delay_factor
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


def get_results_summary(job, results, now):
    summary = [
        f'Job: {job.name} ({job.type})',
        f'Runtime: {now}',
        f'Status: {"PASS" if results["success"] else "FAILED"}'
    ]
    print(results, 'devices' in results, not results["success"])
    if 'devices' in results['result'] and not results["success"]:
        device_status = [
            f'{device}: {"PASS" if device_results["success"] else "FAILED"}'
            for device, device_results in results['result']['devices'].items()
        ]
        summary.append(f'Per-device Status: {", ".join(device_status)}')
    server_url = environ.get('ENMS_SERVER_ADDR', 'http://SERVER_IP')
    logs_url = f'{server_url}/automation/logs/{job.id}/{now}'
    summary.append(f'Logs: {logs_url}')
    return '\n\n'.join(summary)


def scheduler_job(job_id):
    with scheduler.app.app_context():
        job = fetch('Job', id=job_id)
        job.state = 'Running'
        info(f'{job.name}: starting.')
        db.session.commit()
        results, now = job.try_run()
        info(f'{job.name}: finished.')
        job.state = 'Idle'
        if job.send_notification:
            fetch('Job', name=job.send_notification_method).try_run({
                'job': job.serialized,
                'result': get_results_summary(job, results, now)
            })
        db.session.commit()

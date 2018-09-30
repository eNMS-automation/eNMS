from napalm import get_network_driver
from napalm._SUPPORTED_DRIVERS import SUPPORTED_DRIVERS
from netmiko import ConnectHandler
from netmiko.ssh_dispatcher import CLASS_MAPPER

from eNMS import scheduler
from eNMS.base.helpers import get_credentials

netmiko_drivers = sorted(
    driver for driver in CLASS_MAPPER
    if 'telnet' not in driver and 'ssh' not in driver
)

# we exclude "base" from supported drivers
napalm_drivers = SUPPORTED_DRIVERS[1:]


def netmiko_connection(service, device):
    username, password, enable_password = get_credentials(scheduler.app, device)
    return ConnectHandler(
        device_type=service.driver,
        ip=device.ip_address,
        username=username,
        password=password,
        secret=device.enable_password
    )


def napalm_connection(service, device):
    username, password, enable_password = get_credentials(scheduler.app, device)
    driver = get_network_driver(service.driver)
    return driver(
        hostname=device.ip_address,
        username=username,
        password=password,
        optional_args={'secret': enable_password}
    )

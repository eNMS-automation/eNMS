from napalm import get_network_driver
from netmiko import ConnectHandler
from passlib.hash import cisco_type7 as ct7

from eNMS import app


def netmiko_connection(script, task, node):
    if app.production:
        username = 
    else:
        username, password = task.user.name, ct7(task.user.password)
    return ConnectHandler(
        device_type=script.driver,
        ip=node.ip_address,
        username=username,
        password=password,
        secret=node.secret_password
    )


def napalm_connection(script, task, node):
    driver = get_network_driver(node.operating_system)
    if app.production:
    else:
        username, password = task.user.name, ct7(task.user.password)
    return napalm_driver = driver(
        hostname=node.ip_address,
        username=username,
        password=password,
        optional_args={'secret': node.secret_password}
    )
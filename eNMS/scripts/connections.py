from napalm import get_network_driver
from netmiko import ConnectHandler
from passlib.hash import cisco_type7 as ct7

from eNMS import app


def get_credentials(node, task):
    if app.production:
        credentials = app.vault_client.read(
            f'secret/data/object/{node.name}'
        )['data']['data']
        return credentials['username'], credentials['password']
    else:
        return task.user.name, ct7(task.user.password)


def netmiko_connection(script, task, node):
    username, password = get_credentials(node, task)
    return ConnectHandler(
        device_type=script.driver,
        ip=node.ip_address,
        username=username,
        password=password,
        secret=node.secret_password
    )


def napalm_connection(script, task, node):
    username, password = get_credentials(node, task)
    driver = get_network_driver(node.operating_system)
    return driver(
        hostname=node.ip_address,
        username=username,
        password=password,
        optional_args={'secret': node.secret_password}
    )

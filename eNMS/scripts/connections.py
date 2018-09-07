from napalm import get_network_driver
from netmiko import ConnectHandler
from passlib.hash import cisco_type7 as ct7

from eNMS import scheduler


def get_credentials(node, user):
    if scheduler.app.production:
        creds = scheduler.app.vault_client.read(
            f'secret/data/device/{node.name}'
        )['data']['data']
        return creds['username'], creds['password'], creds['secret_password']
    else:
        return user.name, ct7.decode(user.password), node.secret_password


def netmiko_connection(script, task, node):
    username, password, secret_password = get_credentials(node, task.user)
    return ConnectHandler(
        device_type=script.driver,
        ip=node.ip_address,
        username=username,
        password=password,
        secret=node.secret_password
    )


def napalm_connection(script, task, node):
    username, password, secret_password = get_credentials(node, task.user)
    driver = get_network_driver(node.operating_system)
    return driver(
        hostname=node.ip_address,
        username=username,
        password=password,
        optional_args={'secret': secret_password}
    )

from eNMS import use_vault, vault_client


def allowed_file(name, allowed_extensions):
    allowed_syntax = '.' in name
    allowed_extension = name.rsplit('.', 1)[1].lower() in allowed_extensions
    return allowed_syntax and allowed_extension


def write_vault(path, data):
    vault_client.write(f'secret/data/{path}', data=data)


def read_vault(path, property):
    full_path = f'secret/data/{path}/{property}'
    return vault_client.read(full_path)['data']['data'][property]


def get_device_credentials(device):
    return (
        read_vault(f'Device/{device.name}', 'password'),
        read_vault(f'Device/{device.name}', 'enable_password')
    ) if use_vault else (device.password, device.enable_password)


def get_user_credentials(user):
    if use_vault:
        return read_vault(f'User/{user.name}', 'password')
    else:
        return user.password

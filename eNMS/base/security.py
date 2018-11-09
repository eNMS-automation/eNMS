from eNMS import vault_client


def allowed_file(name, allowed_extensions):
    allowed_syntax = '.' in name
    allowed_extension = name.rsplit('.', 1)[1].lower() in allowed_extensions
    return allowed_syntax and allowed_extension


def write_vault(path, data):
    vault_client.write(f'secret/data/{path}', data=data)


def read_vault(path, *properties):
    data = vault_client.read(f'secret/data/{path}')['data']['data']
    return [data[property] for property in properties]


def get_device_credentials(app, device):
    if app.config['USE_VAULT']:
        return read_vault(
            f'Device/{device.name}', 'password', 'enable_password'
        )
    else:
        return device.password, device.enable_password


def get_user_credentials(app, user):
    if app.config['USE_VAULT']:
        return read_vault(f'User/{user.name}', 'password')
    else:
        return user.password

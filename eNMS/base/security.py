from eNMS import vault_client


def allowed_file(name, allowed_extensions):
    allowed_syntax = '.' in name
    allowed_extension = name.rsplit('.', 1)[1].lower() in allowed_extensions
    return allowed_syntax and allowed_extension


def vault_helper(path, data=None):
    if not data:
        return vault_client.read(f'secret/data/{path}')['data']['data']
    else:
        vault_client.write(f'secret/data/{path}', data=data)


def get_device_credentials(app, device):
    if app.config['USE_VAULT']:
        data = vault_helper(f'Device/{device.name}')
        return (
            vault_helper(f'Device/{device.name}')['password'],
            vault_helper(f'Device/{device.name}')['enable_password']
        )
    else:
        return device.password, device.enable_password


def get_user_credentials(app, user):
    if app.config['USE_VAULT']:
        return vault_helper(f'user/{user.name}')['password']
    else:
        return user.password

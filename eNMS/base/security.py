from eNMS import vault_client


def process_kwargs(app, **kwargs):

    else:
        if app.config['USE_VAULT']:
            data = {
                property: kwargs.pop(property, '')
                for property in ()
            }
            
    return 'Link' if 'source' in kwargs else 'Device', kwargs


def allowed_file(name, allowed_extensions):
    allowed_syntax = '.' in name
    allowed_extension = name.rsplit('.', 1)[1].lower() in allowed_extensions
    return allowed_syntax and allowed_extension


def vault_helper(path, data=None):
    vault_path = f'secret/data/{path}'
    if not data:
        return vault_client.read(vault_path)['data']['data']
    else:
        vault_client.write(vault_path, data=data)


def get_device_credentials(app, device):
    if app.config['USE_VAULT']:
        data = vault_helper(app, f'device/{device.name}')
        return data['username'], data['password'], data['enable_password']
    else:
        return device.username, device.password, device.enable_password


def get_user_credentials(app, user):
    if app.config['USE_VAULT']:
        return user.name, vault_helper(app, f'user/{user.name}')['password']
    else:
        return user.name, user.password

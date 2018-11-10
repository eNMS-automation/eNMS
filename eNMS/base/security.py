from eNMS import use_vault, vault_client


def allowed_file(name, allowed_extensions):
    allowed_syntax = '.' in name
    allowed_extension = name.rsplit('.', 1)[1].lower() in allowed_extensions
    return allowed_syntax and allowed_extension


def write_vault(path, data):
    vault_client.write(f'secret/data/{path}', data=data)


def sget(instance, property):
    if use_vault:
        path = f'secret/data/{instance.type}/{instance.name}/{property}'
        return vault_client.read(path)['data']['data'][property]
    else:
        return getattr(instance, property)

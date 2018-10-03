from flask import abort
from flask_login import current_user
from functools import wraps
from sqlalchemy import exc

from eNMS import db


def retrieve(model, **kwargs):
    return db.session.query(model).filter_by(**kwargs).first()


def integrity_rollback(function):
    def wrapper(*a, **kw):
        try:
            function(*a, **kw)
        except (exc.IntegrityError, exc.InvalidRequestError):
            db.session.rollback()
    return wrapper


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.allowed(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def str_dict(input, depth=0):
    tab = '\t' * depth
    if isinstance(input, list):
        result = '\n'
        for element in input:
            result += '{}- {}\n'.format(tab, str_dict(element, depth + 1))
        return result
    elif isinstance(input, dict):
        result = ''
        for key, value in input.items():
            result += '\n{}{}: {}'.format(tab, key, str_dict(value, depth + 1))
        return result
    else:
        return str(input)


def allowed_file(name, allowed_extensions):
    allowed_syntax = '.' in name
    allowed_extension = name.rsplit('.', 1)[1].lower() in allowed_extensions
    return allowed_syntax and allowed_extension


def vault_helper(app, path, data=None):
    vault_path = f'secret/data/{path}'
    if not data:
        return app.vault_client.read(vault_path)['data']['data']
    else:
        app.vault_client.write(vault_path, data=data)


def get_device_credentials(app, device):
    if app.production:
        data = vault_helper(app, f'device/{device.name}')
        return data['username'], data['password'], data['enable_password']
    else:
        return device.username, device.password, device.enable_password


def get_user_credentials(app, user):
    if app.production:
        return user.name, vault_helper(app, f'user/{user.name}')['password']
    else:
        return user.name, user.password

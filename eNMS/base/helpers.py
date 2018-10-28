from flask import abort, jsonify
from flask_login import current_user, login_required
from functools import wraps
from sqlalchemy import Boolean, exc, Integer, String, Float

from eNMS import db


sql_types = {
    'boolean': Boolean,
    'float': Float,
    'integer': Integer,
    'string': String
}


def fetch(model, **kwargs):
    return db.session.query(model).filter_by(**kwargs).first()


def objectify(model, object_list):
    return [fetch(model, id=object_id) for object_id in object_list]


def integrity_rollback(function):
    def wrapper(*a, **kw):
        try:
            function(*a, **kw)
        except (exc.IntegrityError, exc.InvalidRequestError):
            db.session.rollback()
    return wrapper


def permission_required(permission, redirect=True):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if permission and not current_user.allowed(permission):
                if redirect:
                    abort(403)
                else:
                    return jsonify(False)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def route_function(method):
    def route(blueprint, url, permission=None, method=method):
        def outer(func):
            @blueprint.route(url, methods=[method])
            @login_required
            @permission_required(permission, redirect=(method == 'GET'))
            @wraps(func)
            def inner(*args, **kwargs):
                return func(*args, **kwargs)
            return inner
        return outer
    return route


def str_dict(input, depth=0):
    tab = '\t' * depth
    if isinstance(input, list):
        result = '\n'
        for element in input:
            result += f'{tab}- {str_dict(element, depth + 1)}\n'
        return result
    elif isinstance(input, dict):
        result = ''
        for key, value in input.items():
            result += f'\n{tab}{key}: {str_dict(value, depth + 1)}'
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


get, post = route_function('GET'), route_function('POST')

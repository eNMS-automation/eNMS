from flask import abort, jsonify
from flask_login import current_user, login_required
from functools import wraps
from sqlalchemy import exc

from eNMS import db
from eNMS.base.models import classes


def add_classes(*models):
    for model in models:
        classes.update({
            model.__tablename__: model,
            model.__tablename__.lower(): model
        })


def fetch(model, **kwargs):
    return db.session.query(classes[model]).filter_by(**kwargs).first()


def fetch_all(model):
    return classes[model].query.all()


def objectify(model, object_list):
    return [fetch(model, id=object_id) for object_id in object_list]


def delete(model, **kwargs):
    instance = db.session.query(classes[model]).filter_by(**kwargs).first()
    result = instance.serialized
    db.session.delete(instance)
    db.session.commit()
    return result


def serialize(model):
    return classes[model].serialize()


def choices(model):
    return classes[model].choices()


def export(model):
    return classes[model].export()


def get_one(model):
    return classes[model].query.one()


def factory(cls_name, **kwargs):
    if 'id' in kwargs:
        if kwargs['id']:
            instance = fetch(cls_name, id=kwargs['id'])
        else:
            instance = kwargs.pop('id')
    else:
        instance = fetch(cls_name, name=kwargs['name'])
    if instance:
        instance.update(**kwargs)
    else:
        instance = classes[cls_name](**kwargs)
        db.session.add(instance)
    db.session.commit()
    return instance


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


def get(blueprint, url, permission=None, method=['GET']):
    def outer(func):
        @blueprint.route(url, methods=method)
        @login_required
        @permission_required(permission)
        @wraps(func)
        def inner(*args, **kwargs):
            return func(*args, **kwargs)
        return inner
    return outer


def post(blueprint, url, permission=None, method=['POST']):
    def outer(func):
        @blueprint.route(url, methods=method)
        @login_required
        @permission_required(permission, redirect=False)
        @wraps(func)
        def inner(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error = str(e)
                if error == 'Expecting value: line 1 column 1 (char 0)':
                    error = 'Invalid syntax for dictionnary input.'
                return jsonify({'failure': True, 'error': error})
        return inner
    return outer


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

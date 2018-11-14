from flask import abort, jsonify, request, render_template
from flask_login import current_user, login_required
from functools import wraps
from sqlalchemy import exc

from eNMS import db
from eNMS.base.classes import classes
from eNMS.base.properties import (
    boolean_properties,
    list_properties,
    pretty_names,
    property_types
)


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


def fetch_all_visible(model):
    return [
        instance for instance in classes[model].query.all()
        if instance.visible
    ]


def objectify(model, object_list):
    return [fetch(model, id=object_id) for object_id in object_list]


def delete(model, **kwargs):
    instance = db.session.query(classes[model]).filter_by(**kwargs).first()
    if hasattr(instance, 'type') and instance.type == 'Task':
        instance.delete_task()
    result = instance.serialized
    db.session.delete(instance)
    db.session.commit()
    return result


def delete_all(model):
    for instance in fetch_all(model):
        delete(model, id=instance.id)
    db.session.commit()


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


def process_request(function):
    def wrapper(*a, **kw):
        data = request.form.to_dict()
        for property in list_properties:
            if property in request.form:
                data[property] = request.form.getlist(property)
            else:
                data[property] = []
        for property in boolean_properties:
            if property not in request.form:
                data[property] = 'off'
        request.form = data
        return function(*a, **kw)
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


def templated(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        ctx = function(*args, **kwargs) or {}
        if not isinstance(ctx, dict):
            return ctx
        ctx.update({
            'names': pretty_names,
            'property_types': {k: str(v) for k, v in property_types.items()}
        })
        endpoint = request.endpoint.split('.')[-1]
        return render_template(ctx.pop('template', f'{endpoint}.html'), **ctx)
    return decorated_function


def get(blueprint, url, permission=None, method=['GET']):
    def outer(func):
        @blueprint.route(url, methods=method)
        @templated
        @login_required
        @permission_required(permission)
        @wraps(func)
        def inner(*args, **kwargs):
            return func(*args, **kwargs)
        return inner
    return outer


def post(blueprint, url, permission=None):
    def outer(func):
        @blueprint.route(url, methods=['POST'])
        @login_required
        @permission_required(permission, redirect=False)
        @wraps(func)
        @process_request
        def inner(*args, **kwargs):
            # try:
            return func(*args, **kwargs)
            # except Exception as e:
            #     error = str(e)
            #     if error == 'Expecting value: line 1 column 1 (char 0)':
            #         error = 'Invalid syntax for dictionnary input.'
            #     return jsonify({'failure': True, 'error': error})
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

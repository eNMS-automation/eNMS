from collections import Counter
from json.decoder import JSONDecodeError
from logging import info
from flask import redirect, request, url_for
from flask_login import current_user

from eNMS.base import bp
from eNMS.base.classes import classes
from eNMS.base.helpers import (
    delete,
    factory,
    fetch,
    fetch_all,
    fetch_all_visible,
    get,
    post
)
from eNMS.base.properties import (
    default_diagrams_properties,
    reverse_pretty_names,
    type_to_diagram_properties
)


@bp.route('/')
def site_root():
    return redirect(url_for('admin_blueprint.login'))


@get(bp, '/dashboard')
def dashboard():
    return dict(
        properties=type_to_diagram_properties,
        default_properties=default_diagrams_properties,
        counters={cls: len(fetch_all_visible(cls)) for cls in classes}
    )


@post(bp, '/counters/<property>/<type>')
def get_counters(property, type):
    objects = fetch_all(type)
    if property in reverse_pretty_names:
        property = reverse_pretty_names[property]
    return Counter(map(lambda o: str(getattr(o, property)), objects))


@post(bp, '/get/<cls>/<id>', 'View')
def get_instance(cls, id):
    instance = fetch(cls, id=id)
    info(f'{current_user.name}: GET {cls} {instance.name} ({id})')
    return instance.serialized


@post(bp, '/update/<cls>', 'Edit')
def update_instance(cls):
    try:
        instance = factory(cls, **request.form)
        info(
            f'{current_user.name}: UPDATE {cls} '
            f'{instance.name} ({instance.id})'
        )
        return instance.serialized
    except JSONDecodeError:
        return {'error': 'Invalid JSON syntax (JSON field)'}


@post(bp, '/delete/<cls>/<id>', 'Edit')
def delete_instance(cls, id):
    instance = delete(cls, id=id)
    info(f'{current_user.name}: DELETE {cls} {instance["name"]} ({id})')
    return instance


@post(bp, '/shutdown', 'Admin')
def shutdown():
    info(f'{current_user.name}: SHUTDOWN eNMS')
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'

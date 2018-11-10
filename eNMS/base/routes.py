from collections import Counter
from flask import jsonify, redirect, request, url_for

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
    return jsonify(Counter(map(lambda o: str(getattr(o, property)), objects)))


@post(bp, '/get/<cls>/<id>', 'View')
def get_instance(cls, id):
    return jsonify(fetch(cls, id=id).serialized)


@post(bp, '/update/<cls>', 'Edit')
def update_instance(cls):
    return jsonify(factory(cls, **request.form).serialized)


@post(bp, '/delete/<cls>/<id>', 'Edit')
def delete_instance(cls, id):
    return jsonify(delete(cls, id=id))


@post(bp, '/shutdown', 'Admin')
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'

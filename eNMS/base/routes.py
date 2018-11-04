from collections import Counter
from flask import jsonify, render_template, redirect, request, url_for

from eNMS.base import bp
from eNMS.base.classes import classes
from eNMS.base.helpers import fetch_all, get, post
from eNMS.base.properties import (
    default_diagrams_properties,
    pretty_names,
    reverse_pretty_names,
    type_to_diagram_properties
)


@bp.route('/')
def site_root():
    return redirect(url_for('admin_blueprint.login'))


@get(bp, '/dashboard')
def dashboard():
    return render_template(
        'dashboard.html',
        names=pretty_names,
        properties=type_to_diagram_properties,
        default_properties=default_diagrams_properties,
        counters={cls: len(fetch_all(cls)) for cls in classes}
    )


@post(bp, '/process/<cls>', 'Edit Admin Section')
def process_instance(cls):
    return jsonify(factory(cls, **request.form).serialized)


@post(bp, '/get/<cls>/<id>', 'Admin Section')
def get_instance(id):
    return jsonify(fetch(cls, id=user_id).serialized)


@post(bp, '/delete/<user_id>', 'Edit Admin Section')
def delete_instance(user_id):
    return jsonify(delete('User', id=user_id))


@post(bp, '/counters/<property>/<type>')
def get_counters(property, type):
    objects = fetch_all(type)
    if property in reverse_pretty_names:
        property = reverse_pretty_names[property]
    return jsonify(Counter(map(lambda o: str(getattr(o, property)), objects)))


@post(bp, '/shutdown', 'Admin')
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'

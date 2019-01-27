from collections import Counter
from json.decoder import JSONDecodeError
from logging import info
from flask import jsonify, redirect, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import and_

from eNMS import db
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
    table_properties,
    reverse_pretty_names,
    table_static_entries,
    type_to_diagram_properties
)


@bp.route('/')
def site_root():
    return redirect(url_for('admin_blueprint.login'))


@bp.route('/server_side_processing/<table>')
@login_required
def server_side_processing(table):
    start, length = int(request.args['start']), int(request.args['length']) 
    model, properties = classes[table], table_properties[table]
    filtered = db.session.query(model).filter(and_(*[
        getattr(model, property).contains(value)
        for property, value in {
            property: request.args[f'columns[{i}][search][value]']
            for i, property in enumerate(properties)
            if request.args[f'columns[{i}][search][value]']
        }.items()
    ]))
    return jsonify({
        'draw': int(request.args['draw']),
        'recordsTotal': len(model.query.all()),
        'recordsFiltered': len(filtered.all()),
        'data': [
            [getattr(device, property) for property in properties]
            + table_static_entries(table, device)
            for device in filtered.limit(length).offset(start).all()
        ]
    })


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

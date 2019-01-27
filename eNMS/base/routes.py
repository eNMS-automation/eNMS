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
    filters = {
        property: request.args[f'columns[{i}][search][value]']
        for i, property in enumerate(properties)
        if request.args[f'columns[{i}][search][value]']
    }
    filtered = db.session.query(model).filter(and_(*[
        getattr(model, property).contains(value)
        for property, value in filters.items()
    ]))
    data = []
    for device in filtered.limit(length).offset(start).all():
        device = device.serialized
        device_data = [device[p] for p in properties] + ['a'
        # f'''<button type="button" class="btn btn-info btn-xs"
        # onclick="deviceAutomationModal('{device["id"]}')">
        # Automation</button>''',
        # f'''<button type="button" class="btn btn-success btn-xs"
        # onclick="connectionParametersModal('{device["id"]}')">
        # Connect</button>''',
        # f'''<button type="button" class="btn btn-primary btn-xs"
        # onclick="showTypeModal('device', '{device["id"]}')">Edit</button>''',
        # f'''<button type="button" class="btn btn-primary btn-xs"
        # onclick="showTypeModal('device', '{device["id"]}', true)">
        # Duplicate</button>''',
        # f'''<button type="button" class="btn btn-danger btn-xs"
        # onclick="confirmDeletion('device', '{device["id"]}')">
        # Delete</button>'''
    ]*3
        data.append(device_data)
    return jsonify({
        'draw': int(request.args['draw']),
        'recordsTotal': len(model.all()),
        'recordsFiltered': len(filtered.all()),
        'data': data
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

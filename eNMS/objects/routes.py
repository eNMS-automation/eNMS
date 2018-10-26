from collections import defaultdict
from flask import current_app as app, jsonify, render_template, request
from flask_login import current_user
from pathlib import Path
from subprocess import Popen
from werkzeug.utils import secure_filename
from xlrd import open_workbook
from xlrd.biffh import XLRDError
from xlwt import Workbook

from eNMS import db
from eNMS.admin.models import Parameters
from eNMS.base.custom_base import factory
from eNMS.base.helpers import (
    allowed_file,
    fetch,
    get,
    get_device_credentials,
    get_user_credentials,
    post,
    vault_helper
)
from eNMS.objects import bp
from eNMS.objects.forms import AddLink, AddDevice, AddPoolForm, PoolObjectsForm
from eNMS.objects.models import Link, Device, Pool
from eNMS.base.properties import (
    boolean_properties,
    device_public_properties,
    link_public_properties,
    pool_public_properties,
    pretty_names,
    cls_to_properties
)


def process_kwargs(app, **kwargs):
    if 'source' in kwargs:
        source = fetch(Device, name=kwargs.pop('source'))
        destination = fetch(Device, name=kwargs.pop('destination'))
        kwargs.update({
            'source_id': source.id,
            'destination_id': destination.id,
            'source': source,
            'destination': destination
        })
    else:
        if app.config['USE_VAULT']:
            data = {
                property: kwargs.pop(property, '')
                for property in ('username', 'password', 'enable_password')
            }
            vault_helper(app, f'device/{kwargs["name"]}', data)
    return Link if 'source' in kwargs else Device, kwargs


@get(bp, '/device_management', 'Inventory Section')
def device_management():
    return render_template(
        'device_management.html',
        names=pretty_names,
        fields=device_public_properties,
        devices=Device.serialize(),
        add_device_form=AddDevice(request.form)
    )


@get(bp, '/link_management', 'Inventory Section')
def link_management():
    add_link_form = AddLink(request.form)
    all_devices = [(n.name, n.name) for n in Device.query.all()]
    add_link_form.source.choices = all_devices
    add_link_form.destination.choices = all_devices
    return render_template(
        'link_management.html',
        names=pretty_names,
        fields=link_public_properties,
        links=Link.serialize(),
        add_link_form=add_link_form
    )


@get(bp, '/pool_management', 'Inventory Section')
def pool_management():
    pool_object_form = PoolObjectsForm(request.form)
    pool_object_form.devices.choices = Device.choices()
    pool_object_form.links.choices = Link.choices()
    return render_template(
        'pool_management.html',
        form=AddPoolForm(request.form),
        pool_object_form=pool_object_form,
        names=pretty_names,
        fields=pool_public_properties,
        pools=Pool.serialize()
    )


@post(bp, '/get/<obj_type>/<id>', 'Inventory Section')
def get_object(obj_type, id):
    device = fetch(Device if obj_type == 'device' else Link, id=id)
    return jsonify(device.serialized)


@post(bp, '/connection/<id>', 'Connect to device')
def connection(id):
    parameters, device = Parameters.query.one(), fetch(Device, id=id)
    cmd = [str(app.path / 'applications' / 'gotty'), '-w']
    port, ip = parameters.get_gotty_port(), device.ip_address
    cmd.extend(['-p', str(port)])
    if 'accept-once' in request.form:
        cmd.append('--once')
    if 'multiplexing' in request.form:
        cmd.extend(f'tmux new -A -s gotty{port}'.split())
    if app.config['GOTTY_BYPASS_KEY_PROMPT']:
        options = '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
    else:
        options = ''
    if 'authentication' in request.form:
        if request.form['credentials'] == 'device':
            login, pwd, _ = get_device_credentials(app, device)
        else:
            login, pwd = get_user_credentials(app, current_user)
        cmd.extend(f'sshpass -p {pwd} ssh {options} {login}@{ip}'.split())
    else:
        cmd.extend(f'ssh {options} {ip}'.split())
    cmd.extend(f'-p {device.port}'.split())
    Popen(cmd)
    return jsonify({
        'device': device.name,
        'port': port,
        'redirection': app.config['GOTTY_PORT_REDIRECTION'],
        'server_addr': app.config['GOTTY_SERVER_ADDR']
    })


@post(bp, '/edit_object', 'Edit Inventory Section')
def edit_object():
    print(request.form.to_dict())
    cls, kwargs = process_kwargs(app, **request.form.to_dict())
    obj = factory(cls, **kwargs)
    return jsonify(obj.serialized)


@post(bp, '/delete/<obj_type>/<obj_id>', 'Edit Inventory Section')
def delete_object(obj_type, obj_id):
    cls = Device if obj_type == 'device' else Link
    obj = fetch(cls, id=obj_id)
    db.session.delete(obj)
    db.session.commit()
    return jsonify({'name': obj.name})


@post(bp, '/import_topology', 'Edit Inventory Section')
def import_topology():
    objects, file = defaultdict(list), request.files['file']
    if allowed_file(secure_filename(file.filename), {'xls', 'xlsx'}):
        book = open_workbook(file_contents=file.read())
        for object_type in ('Device', 'Link'):
            try:
                sheet = book.sheet_by_name(object_type)
            except XLRDError:
                continue
            properties = sheet.row_values(0)
            for row_index in range(1, sheet.nrows):
                values = dict(zip(properties, sheet.row_values(row_index)))
                cls, kwargs = process_kwargs(app, **values)
                objects[object_type].append(factory(cls, **kwargs).serialized)
            db.session.commit()
    return jsonify(objects)


@post(bp, '/export_topology', 'Inventory Section')
def export_topology():
    workbook = Workbook()
    for cls in (Device, Link):
        sheet, objects = workbook.add_sheet(cls.__tablename__), cls.serialize()
        for index, property in enumerate(cls_to_properties[cls.__tablename__]):
            sheet.write(0, index, property)
            for obj_index, obj in enumerate(objects, 1):
                sheet.write(obj_index, index, obj[property])
    workbook.save(Path.cwd() / 'projects' / 'objects.xls')
    return jsonify(True)


@post(bp, '/process_pool', 'Edit Inventory Section')
def process_pool():
    form = request.form.to_dict()
    for property in boolean_properties:
        if property not in form:
            form[property] = 'off'
    return jsonify(factory(Pool, **form).serialized)


@post(bp, '/get_pool/<pool_id>', 'Inventory Section')
def get_pool(pool_id):
    return jsonify(fetch(Pool, id=pool_id).get_properties())


@post(bp, '/get_pool_objects/<pool_id>', 'Inventory Section')
def get_pool_objects(pool_id):
    return jsonify(fetch(Pool, id=pool_id).serialized)


@post(bp, '/save_pool_objects/<pool_id>', 'Edit Inventory Section')
def save_pool_objects(pool_id):
    pool = fetch(Pool, id=pool_id)
    pool.devices = [
        fetch(Device, id=id) for id in request.form.getlist('devices')
    ]
    pool.links = [fetch(Link, id=id) for id in request.form.getlist('links')]
    db.session.commit()
    return jsonify(pool.name)


@post(bp, '/pool_objects/<pool_id>', 'Inventory Section')
def filter_pool_objects(pool_id):
    pool = fetch(Pool, id=pool_id)
    return jsonify(pool.filter_objects())


@post(bp, '/update_pools', 'Edit Inventory Section')
def update_pools():
    for pool in Pool.query.all():
        pool.compute_pool()
    db.session.commit()
    return jsonify({'success': True})


@post(bp, '/delete_pool/<pool_id>', 'Edit Inventory Section')
def delete_pool(pool_id):
    pool = fetch(Pool, id=pool_id)
    db.session.delete(pool)
    db.session.commit()
    return jsonify(pool.name)

from collections import defaultdict
from flask import current_app, jsonify, render_template, request, send_file
from flask_login import login_required
from passlib.hash import cisco_type7
from pathlib import Path
from werkzeug.utils import secure_filename
from xlrd import open_workbook
from xlrd.biffh import XLRDError
import xlwt


from eNMS import db
from eNMS.base.custom_base import factory
from eNMS.base.helpers import allowed_file, retrieve
from eNMS.objects import blueprint
from eNMS.objects.forms import AddLink, AddDevice, AddPoolForm, PoolObjectsForm
from eNMS.objects.models import Link, Device, Pool
from eNMS.base.properties import (
    link_public_properties,
    device_public_properties,
    pool_public_properties,
    pretty_names,
    cls_to_properties
)


def process_kwargs(app, **kwargs):
    if 'source' in kwargs:
        source = retrieve(Device, name=kwargs.pop('source'))
        destination = retrieve(Device, name=kwargs.pop('destination'))
        kwargs.update({
            'source_id': source.id,
            'destination_id': destination.id,
            'source': source,
            'destination': destination
        })
    else:
        if app.production:
            app.vault_client.write(
                f'secret/data/device/{kwargs["name"]}',
                data={
                    'username': kwargs.pop('username', ''),
                    'password': kwargs.pop('password', ''),
                    'secret_password': kwargs.pop('secret_password', '')
                }
            )
        else:
            for arg in ('password', 'secret_password'):
                kwargs[arg] = cisco_type7.hash(kwargs.get(arg, ''))
    return Link if 'source' in kwargs else Device, kwargs


@blueprint.route('/device_management', methods=['GET', 'POST'])
@login_required
def device_management():
    return render_template(
        'device_management.html',
        names=pretty_names,
        fields=device_public_properties,
        devices=Device.serialize(),
        add_device_form=AddDevice(request.form)
    )


@blueprint.route('/link_management', methods=['GET', 'POST'])
@login_required
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


@blueprint.route('/object_download')
@login_required
def objects_download():
    devices = Device.serialize()
    ws = {}
    wb = xlwt.Workbook()
    style0 = xlwt.easyxf(
        'font: name Times New Roman, color-index black, bold on',
        num_format_str='#,##0.00'
    )
    style1 = xlwt.easyxf(num_format_str='#,##0.00')
    header_index = 0
    for tab, header in cls_to_properties.items():
        column = 0
        ws[tab] = wb.add_sheet(tab)
        ws[tab].row_index = 1
        for entry in header:
            ws[tab].write(header_index, column, entry, style0)
            column = column + 1
    column = 0
    for device in devices:
        for k, v in device.items():
            if k is not 'id':
                try:
                    ws[device['type']].write(
                        ws[device['type']].row_index,
                        column,
                        v,
                        style1
                    )
                    column = column + 1
                except Exception:
                    continue
        column = 0
        ws[device['type']].row_index = ws[device['type']].row_index + 1
    obj_file = Path.cwd() / 'projects' / 'objects.xls'
    wb.save(str(obj_file))
    sfd = send_file(
        filename_or_fp=str(obj_file),
        as_attachment=True,
        attachment_filename='objects.xls'
    )
    return sfd


@blueprint.route('/pool_management')
@login_required
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


@blueprint.route('/get/<obj_type>/<obj_id>', methods=['POST'])
@login_required
def get_object(obj_type, obj_id):
    if obj_type == 'device':
        cls, properties = Device, device_public_properties
    else:
        cls, properties = Link, link_public_properties
    obj = retrieve(cls, id=obj_id)
    obj_properties = {
        property: str(getattr(obj, property))
        for property in properties
    }
    return jsonify(obj_properties)


@blueprint.route('/edit_object', methods=['POST'])
@login_required
def edit_object():
    cls, kwargs = process_kwargs(current_app, **request.form.to_dict())
    obj = factory(cls, **kwargs)
    return jsonify(obj.serialized)


@blueprint.route('/delete/<obj_type>/<obj_id>', methods=['POST'])
@login_required
def delete_object(obj_type, obj_id):
    cls = Device if obj_type == 'device' else Link
    obj = retrieve(cls, id=obj_id)
    db.session.delete(obj)
    db.session.commit()
    return jsonify({'name': obj.name})


@blueprint.route('/import_topology', methods=['POST'])
@login_required
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
                cls, kwargs = process_kwargs(current_app, **values)
                objects[object_type].append(factory(cls, **kwargs).serialized)
            db.session.commit()
    return jsonify(objects)


@blueprint.route('/process_pool', methods=['POST'])
@login_required
def process_pool():
    return jsonify(factory(Pool, **request.form.to_dict()).serialized)


@blueprint.route('/get_pool/<pool_id>', methods=['POST'])
@login_required
def get_pool(pool_id):
    return jsonify(retrieve(Pool, id=pool_id).get_properties())


@blueprint.route('/get_pool_objects/<pool_id>', methods=['POST'])
@login_required
def get_pool_objects(pool_id):
    return jsonify(retrieve(Pool, id=pool_id).serialized)


@blueprint.route('/save_pool_objects/<pool_id>', methods=['POST'])
@login_required
def save_pool_objects(pool_id):
    pool = retrieve(Pool, id=pool_id)
    pool.devices = [
        retrieve(Device, id=id) for id in request.form.getlist('devices')
    ]
    pool.links = [retrieve(Link, id=id) for id in request.form.getlist('links')]
    db.session.commit()
    return jsonify(pool.name)


@blueprint.route('/pool_objects/<pool_id>', methods=['POST'])
@login_required
def filter_pool_objects(pool_id):
    pool = retrieve(Pool, id=pool_id)
    return jsonify(pool.filter_objects())


@blueprint.route('/update_pools', methods=['POST'])
@login_required
def update_pools():
    for pool in Pool.query.all():
        pool.compute_pool()
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/delete_pool/<pool_id>', methods=['POST'])
@login_required
def delete_pool(pool_id):
    pool = retrieve(Pool, id=pool_id)
    db.session.delete(pool)
    db.session.commit()
    return jsonify(pool.name)

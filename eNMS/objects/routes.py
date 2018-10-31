from collections import defaultdict
from flask import current_app as app, jsonify, render_template, request
from flask_login import current_user
from os import makedirs
from os.path import exists
from pathlib import Path
from pynetbox import api as netbox_api
from requests import get as http_get
from subprocess import Popen
from werkzeug.utils import secure_filename
from xlrd import open_workbook
from xlrd.biffh import XLRDError
from xlwt import Workbook
from yaml import dump, load

from eNMS import db
from eNMS.base.helpers import (
    choices,
    delete,
    export,
    factory,
    fetch,
    fetch_all,
    get,
    get_one,
    objectify,
    post,
    serialize
)
from eNMS.base.security import (
    allowed_file,
    get_device_credentials,
    get_user_credentials,
    process_kwargs
)
from eNMS.objects import bp
from eNMS.objects.forms import (
    AddLink,
    AddDevice,
    AddPoolForm,
    ImportExportForm,
    NetboxForm,
    OpenNmsForm,
    PoolObjectsForm
)
from eNMS.base.properties import (
    boolean_properties,
    device_public_properties,
    export_properties,
    import_properties,
    link_table_properties,
    pool_table_properties,
    pretty_names,
    serialization_properties
)


@get(bp, '/device_management', 'Inventory Section')
def device_management():
    return render_template(
        'device_management.html',
        names=pretty_names,
        fields=device_public_properties,
        devices=serialize('Device'),
        add_device_form=AddDevice(request.form)
    )


@get(bp, '/link_management', 'Inventory Section')
def link_management():
    add_link_form = AddLink(request.form)
    devices = [(l.name, l.name) for l in fetch_all('Device')]
    add_link_form.source_name.choices = devices
    add_link_form.destination_name.choices = devices
    return render_template(
        'link_management.html',
        names=pretty_names,
        fields=link_table_properties,
        links=serialize('Link'),
        add_link_form=add_link_form
    )


@get(bp, '/pool_management', 'Inventory Section')
def pool_management():
    pool_object_form = PoolObjectsForm(request.form)
    pool_object_form.devices.choices = choices('Device')
    pool_object_form.links.choices = choices('Link')
    return render_template(
        'pool_management.html',
        form=AddPoolForm(request.form),
        pool_object_form=pool_object_form,
        names=pretty_names,
        fields=pool_table_properties,
        pools=serialize('Pool')
    )


@get(bp, '/import_export', 'Inventory Section')
def import_export():
    return render_template(
        'import_export.html',
        import_export_form=ImportExportForm(request.form),
        netbox_form=NetboxForm(request.form),
        opennms_form=OpenNmsForm(request.form),
        parameters=get_one('Parameters'),
    )


@post(bp, '/get/<obj_type>/<id>', 'Inventory Section')
def get_object(obj_type, id):
    return jsonify(fetch(obj_type.capitalize(), id=id).serialized)


@post(bp, '/connection/<id>', 'Connect to device')
def connection(id):
    parameters, device = get_one('Parameters'), fetch('Device', id=id)
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
    cls, kwargs = process_kwargs(app, **request.form.to_dict())
    return jsonify(factory(cls, **kwargs).serialized)


@post(bp, '/delete/<obj_type>/<obj_id>', 'Edit Inventory Section')
def delete_object(obj_type, obj_id):
    return jsonify(delete(obj_type.capitalize(), id=obj_id))


@post(bp, '/process_pool', 'Edit Inventory Section')
def process_pool():
    form = request.form.to_dict()
    for property in boolean_properties:
        if property not in form:
            form[property] = 'off'
    return jsonify(factory('Pool', **form).serialized)


@post(bp, '/get/pool/<pool_id>', 'Inventory Section')
def get_pool(pool_id):
    return jsonify(fetch('Pool', id=pool_id).serialized)


@post(bp, '/save_pool_objects/<pool_id>', 'Edit Inventory Section')
def save_pool_objects(pool_id):
    pool = fetch('Pool', id=pool_id)
    pool.devices = objectify('Device', request.form.getlist('devices'))
    pool.links = objectify('Link', request.form.getlist('links'))
    db.session.commit()
    return jsonify(pool.name)


@post(bp, '/pool_objects/<pool_id>', 'Inventory Section')
def filter_pool_objects(pool_id):
    return jsonify(fetch('Pool', id=pool_id).filter_objects())


@post(bp, '/update_pools', 'Edit Inventory Section')
def update_pools():
    for pool in fetch_all('Pool'):
        pool.compute_pool()
    db.session.commit()
    return jsonify(True)


@post(bp, '/delete_pool/<pool_id>', 'Edit Inventory Section')
def delete_pool(pool_id):
    return jsonify(delete('Pool', id=pool_id))


@post(bp, '/import_topology', 'Edit Inventory Section')
def import_topology():
    objects, file = defaultdict(list), request.files['file']
    if allowed_file(secure_filename(file.filename), {'xls', 'xlsx'}):
        book = open_workbook(file_contents=file.read())
        for obj_type in ('Device', 'Link'):
            try:
                sheet = book.sheet_by_name(obj_type)
            except XLRDError:
                continue
            properties = sheet.row_values(0)
            for row_index in range(1, sheet.nrows):
                values = dict(zip(properties, sheet.row_values(row_index)))
                cls, kwargs = process_kwargs(app, **values)
                objects[obj_type].append(factory(cls, **kwargs).serialized)
            db.session.commit()
    return jsonify(objects)


@post(bp, '/export_topology', 'Inventory Section')
def export_topology():
    workbook = Workbook()
    for obj_type in ('Device', 'Link'):
        sheet = workbook.add_sheet(obj_type)
        for index, property in enumerate(export_properties[obj_type]):
            sheet.write(0, index, property)
            for obj_index, obj in enumerate(serialize(obj_type), 1):
                sheet.write(obj_index, index, obj[property])
    workbook.save(Path.cwd() / 'projects' / 'objects.xls')
    return jsonify(True)


@post(bp, '/migration_export', 'Admin Section')
def migration_export():
    name = request.form['name']
    for cls_name in request.form.getlist('export'):
        path = app.path / 'migrations' / 'import_export' / name
        if not exists(path):
            makedirs(path)
        with open(path / f'{cls_name}.yaml', 'w') as migration_file:
            dump(export(cls_name), migration_file, default_flow_style=False)
    return jsonify(True)


@post(bp, '/migration_import', 'Admin Section')
def migration_import():
    name = request.form['name']
    for cls in request.form.getlist('export'):
        path = app.path / 'migrations' / 'import_export' / name / f'{cls}.yaml'
        with open(path, 'r') as migration_file:
            for obj_data in load(migration_file):
                cls_name = obj_data.pop('type') if cls == 'Service' else cls
                obj = {}
                for property, value in obj_data.items():
                    if property not in import_properties[cls]:
                        continue
                    elif property in serialization_properties:
                        model = serialization_properties[property]
                        obj[property] = fetch(model, id=value)
                    elif property[:-1] in serialization_properties:
                        model = serialization_properties[property[:-1]]
                        obj[property] = objectify(model, value)
                    else:
                        obj[property] = value
                factory(cls_name, **obj)
    return jsonify(True)


@post(bp, '/query_opennms', 'Edit objects')
def query_opennms():
    parameters = get_one('Parameters')
    login, password = parameters.opennms_login, request.form['password']
    parameters.update(**request.form.to_dict())
    db.session.commit()
    json_devices = http_get(
        parameters.opennms_devices,
        headers={'Accept': 'application/json'},
        auth=(login, password)
    ).json()['node']
    devices = {
        device['id']:
            {
            'name': device.get('label', device['id']),
            'description': device['assetRecord'].get('description', ''),
            'location': device['assetRecord'].get('building', ''),
            'vendor': device['assetRecord'].get('manufacturer', ''),
            'model': device['assetRecord'].get('modelNumber', ''),
            'operating_system': device.get('operatingSystem', ''),
            'os_version': device['assetRecord'].get('sysDescription', ''),
            'longitude': device['assetRecord'].get('longitude', 0.),
            'latitude': device['assetRecord'].get('latitude', 0.),
            'subtype': request.form['subtype']
        } for device in json_devices
    }

    for device in list(devices):
        link = http_get(
            f'{parameters.opennms_rest_api}/nodes/{device}/ipinterfaces',
            headers={'Accept': 'application/json'},
            auth=(login, password)
        ).json()
        for interface in link['ipInterface']:
            if interface['snmpPrimary'] == 'P':
                devices[device]['ip_address'] = interface['ipAddress']
                factory('Device', **devices[device])
    db.session.commit()
    return jsonify(True)


@post(bp, '/query_netbox', 'Edit objects')
def query_netbox():
    nb = netbox_api(
        request.form['netbox_address'],
        token=request.form['netbox_token']
    )
    for device in nb.dcim.devices.all():
        device_ip = device.primary_ip4 or device.primary_ip6
        factory('Device', **{
            'name': device.name,
            'ip_address': str(device_ip).split('/')[0],
            'subtype': request.form['netbox_type'],
            'longitude': 0.,
            'latitude': 0.
        })
    return jsonify(True)

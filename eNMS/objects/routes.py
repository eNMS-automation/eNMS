from flask import current_app as app, jsonify, request
from flask_login import current_user
from logging import info
from pathlib import Path
from pynetbox import api as netbox_api
from requests import get as http_get
from subprocess import Popen
from werkzeug.utils import secure_filename
from xlrd import open_workbook
from xlrd.biffh import XLRDError
from xlwt import Workbook

from eNMS import db
from eNMS.base.helpers import (
    delete_all,
    factory,
    fetch,
    fetch_all,
    get,
    get_one,
    objectify,
    post,
    serialize
)
from eNMS.objects import bp
from eNMS.objects.forms import (
    AddLink,
    AddDevice,
    AddPoolForm,
    NetboxForm,
    OpenNmsForm,
    PoolObjectsForm
)
from eNMS.objects.helpers import allowed_file
from eNMS.base.properties import (
    device_public_properties,
    export_properties,
    link_table_properties,
    pool_table_properties
)


@get(bp, '/device_management', 'View')
def device_management():
    return dict(
        fields=device_public_properties,
        devices=serialize('Device'),
        add_device_form=AddDevice(request.form)
    )


@get(bp, '/link_management', 'View')
def link_management():
    return dict(
        fields=link_table_properties,
        links=serialize('Link'),
        add_link_form=AddLink(request.form, 'Link')
    )


@get(bp, '/pool_management', 'View')
def pool_management():
    return dict(
        form=AddPoolForm(request.form),
        pool_object_form=PoolObjectsForm(request.form, 'Pool'),
        fields=pool_table_properties,
        pools=serialize('Pool')
    )


@get(bp, '/import_export', 'View')
def import_export():
    return dict(
        netbox_form=NetboxForm(request.form),
        opennms_form=OpenNmsForm(request.form),
        parameters=get_one('Parameters'),
    )


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
            login, pwd = device.username, device.password
        else:
            login, pwd = current_user.name, current_user.password
        cmd.extend(f'sshpass -p {pwd} ssh {options} {login}@{ip}'.split())
    else:
        cmd.extend(f'ssh {options} {ip}'.split())
    cmd.extend(f'-p {device.port}'.split())
    Popen(cmd)
    return jsonify({
        'device': device.name,
        'port': port,
        'redirection': app.config['GOTTY_PORT_REDIRECTION'],
        'server_addr': app.config['ENMS_SERVER_ADDR']
    })


@post(bp, '/save_pool_objects/<id>', 'Edit')
def save_pool_objects(id):
    pool = fetch('Pool', id=id)
    pool.devices = objectify('Device', request.form['devices'])
    pool.links = objectify('Link', request.form['links'])
    db.session.commit()
    return jsonify(pool.serialized)


@post(bp, '/pool_objects/<pool_id>', 'View')
def filter_pool_objects(pool_id):
    return jsonify(fetch('Pool', id=pool_id).filter_objects())


@post(bp, '/update_pools', 'Edit')
def update_pools():
    for pool in fetch_all('Pool'):
        pool.compute_pool()
    db.session.commit()
    return jsonify(True)


@post(bp, '/import_topology', 'Edit')
def import_topology():
    if request.form.get('replace', None) == 'y':
        delete_all('Device')
    if request.form.get('update-pools', None) == 'y':
        for pool in fetch_all('Pool'):
            pool.compute_pool()
        db.session.commit()
    file, result = request.files['file'], 'Topology successfully imported.'
    if allowed_file(secure_filename(file.filename), {'xls', 'xlsx'}):
        book = open_workbook(file_contents=file.read())
        for obj_type in ('Device', 'Link'):
            try:
                sheet = book.sheet_by_name(obj_type)
            except XLRDError:
                continue
            properties = sheet.row_values(0)
            for row_index in range(1, sheet.nrows):
                prop = dict(zip(properties, sheet.row_values(row_index)))
                try:
                    factory(obj_type, **prop).serialized
                except Exception as e:
                    info(f'{str(prop)} could not be imported ({str(e)})')
                    result = 'Partial import (see logs).'
            db.session.commit()
    return jsonify(result)


@post(bp, '/export_topology', 'View')
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


@post(bp, '/query_opennms', 'Edit')
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


@post(bp, '/query_netbox', 'Edit')
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

from flask import current_app as app, request
from flask_login import current_user
from pynetbox import api as netbox_api
from requests import get as http_get
from subprocess import Popen

from eNMS import db
from eNMS.base.helpers import (
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
    DeviceAutomationForm,
    ImportExportForm,
    LibreNmsForm,
    NetboxForm,
    OpenNmsForm,
    PoolObjectsForm
)
from eNMS.objects.helpers import object_export, object_import
from eNMS.base.properties import (
    device_public_properties,
    link_table_properties,
    pool_table_properties
)


@get(bp, '/device_management', 'View')
def device_management():
    return dict(
        fields=device_public_properties,
        devices=serialize('Device'),
        add_device_form=AddDevice(request.form),
        device_automation_form=DeviceAutomationForm(request.form)
    )


@get(bp, '/link_management', 'View')
def link_management():
    return dict(
        fields=link_table_properties,
        links=serialize('Link'),
        add_link_form=AddLink(request.form)
    )


@get(bp, '/pool_management', 'View')
def pool_management():
    return dict(
        form=AddPoolForm(request.form),
        pool_object_form=PoolObjectsForm(request.form),
        fields=pool_table_properties,
        pools=serialize('Pool')
    )


@get(bp, '/import_export', 'View')
def import_export():
    return dict(
        import_export_form=ImportExportForm(request.form),
        librenms_form=LibreNmsForm(request.form),
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
    return {
        'device': device.name,
        'port': port,
        'redirection': app.config['GOTTY_PORT_REDIRECTION'],
        'server_addr': app.config['ENMS_SERVER_ADDR']
    }


@post(bp, '/save_device_jobs/<id>', 'Edit')
def save_device_jobs(id):
    fetch('Device', id=id).jobs = objectify('Job', request.form['jobs'])
    db.session.commit()
    return True


@post(bp, '/save_pool_objects/<id>', 'Edit')
def save_pool_objects(id):
    pool = fetch('Pool', id=id)
    pool.devices = objectify('Device', request.form['devices'])
    pool.links = objectify('Link', request.form['links'])
    db.session.commit()
    return pool.serialized


@post(bp, '/pool_objects/<pool_id>', 'View')
def filter_pool_objects(pool_id):
    return fetch('Pool', id=pool_id).filter_objects()


@post(bp, '/update_pool/<pool>', 'Edit')
def update_pools(pool):
    if pool == 'all':
        for pool in fetch_all('Pool'):
            pool.compute_pool()
    else:
        fetch('Pool', id=pool).compute_pool()
    db.session.commit()
    return True


@post(bp, '/import_topology', 'Edit')
def import_topology():
    return object_import(request.form, request.files['file'])


@post(bp, '/export_topology', 'View')
def export_topology():
    return object_export(request.form, app.path)


@post(bp, '/query_opennms', 'Edit')
def query_opennms():
    parameters = get_one('Parameters')
    login, password = parameters.opennms_login, request.form['password']
    parameters.update(**request.form)
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
    return True


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
    return True

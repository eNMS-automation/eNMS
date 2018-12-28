from datetime import datetime
from difflib import SequenceMatcher
from flask import current_app as app, request, send_file
from flask_login import current_user
from git import Repo
from pynetbox import api as netbox_api
from re import search
from requests import get as http_get
from subprocess import Popen

from eNMS.main import db
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
from eNMS.inventory import bp
from eNMS.inventory.forms import (
    AddDevice,
    AddLink,
    AddPoolForm,
    CompareConfigurationsForm,
    ConfigurationManagementForm,
    ConfigurationParametersForm,
    DeviceAutomationForm,
    GottyConnectionForm,
    ImportExportForm,
    LibreNmsForm,
    NetboxForm,
    OpenNmsForm,
    PollerForm,
    PoolObjectsForm,
    SearchConfigurationForm
)
from eNMS.inventory.helpers import object_export, object_import
from eNMS.base.properties import (
    device_configuration_properties,
    device_table_properties,
    link_table_properties,
    pool_table_properties
)


@get(bp, '/device_management', 'View')
def device_management():
    return dict(
        fields=device_table_properties,
        devices=serialize('Device'),
        add_device_form=AddDevice(request.form),
        device_automation_form=DeviceAutomationForm(request.form),
        gotty_connection_form=GottyConnectionForm(request.form)
    )


@get(bp, '/configuration_management', 'View')
def configuration_management():
    return dict(
        fields=device_configuration_properties,
        devices=serialize('Device'),
        compare_configurations_form=CompareConfigurationsForm(request.form),
        configuration_parameters_form=ConfigurationParametersForm(request.form),
        add_device_form=ConfigurationManagementForm(request.form),
        gotty_connection_form=GottyConnectionForm(request.form),
        poller_form=PollerForm(request.form),
        search_configurations_form=SearchConfigurationForm(request.form)
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


@get(bp, '/download_configuration/<name>', 'View')
def download_configuration(name):
    send_file(
        filename_or_fp=str(app.path / 'git' / 'configurations' / name),
        as_attachment=True,
        attachment_filename=f'configuration_{name}.txt'
    )


@post(bp, '/connection/<id>', 'Connect to device')
def connection(id):
    parameters, device = get_one('Parameters'), fetch('Device', id=id)
    cmd = [str(app.path / 'applications' / 'gotty'), '-w']
    port, protocol = parameters.get_gotty_port(), request.form['protocol']
    address = getattr(device, request.form['address'])
    cmd.extend(['-p', str(port)])
    if 'accept-once' in request.form:
        cmd.append('--once')
    if 'multiplexing' in request.form:
        cmd.extend(f'tmux new -A -s gotty{port}'.split())
    if app.config['GOTTY_BYPASS_KEY_PROMPT']:
        options = '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
    else:
        options = ''
    if protocol == 'telnet':
        cmd.extend(f'telnet {address}'.split())
    elif 'authentication' in request.form:
        if request.form['credentials'] == 'device':
            login, pwd = device.username, device.password
        else:
            login, pwd = current_user.name, current_user.password
        cmd.extend(f'sshpass -p {pwd} ssh {options} {login}@{address}'.split())
    else:
        cmd.extend(f'ssh {options} {address}'.split())
    if protocol != 'telnet':
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


@post(bp, '/query_librenms', 'Edit')
def query_librenms():
    devices = http_get(
        f'{request.form["librenms_address"]}/api/v0/devices',
        headers={'X-Auth-Token': request.form['librenms_token']}
    ).json()['devices']
    for device in devices:
        factory('Device', **{
            'name': device['hostname'],
            'ip_address': device['ip'] or device['hostname'],
            'subtype': request.form['librenms_type'],
            'longitude': 0.,
            'latitude': 0.
        })
    db.session.commit()
    return True


@post(bp, '/configure_poller', 'Edit')
def configure_poller():
    parameters = get_one('Parameters')
    remote_git = request.form['remote_git_repository']
    if parameters.git_repository_configurations != remote_git:
        Repo.clone_from(remote_git, app.path / 'git' / 'configurations')
        parameters.git_repository_configurations = remote_git
    service = fetch('Service', name='configuration_backup')
    task = fetch('Task', name='configuration_backup')
    service.devices = objectify('Device', request.form.get('devices', ''))
    service.pools = objectify('Pool', request.form.get('pools', ''))
    task.frequency = request.form['polling_frequency']
    db.session.commit()
    task.reschedule()
    return True


@post(bp, '/get_configurations/<id>', 'View')
def get_configurations(id):
    return {str(k): v for k, v in fetch('Device', id=id).configurations.items()}


@post(bp, '/get_diff/<device_id>/<v1>/<v2>', 'View')
def get_diff(device_id, v1, v2, n1=None, n2=None):
    device = fetch('Device', id=device_id)
    v1, v2 = [datetime.strptime(d, '%Y-%m-%d %H:%M:%S.%f') for d in (v1, v2)]
    first = device.configurations[v1].splitlines()
    second = device.configurations[v2].splitlines()
    opcodes = SequenceMatcher(None, first, second).get_opcodes()
    return {'first': first, 'second': second, 'opcodes': opcodes}


@post(bp, '/clear_configurations/<device_id>', 'Edit')
def clear_configurations(device_id):
    fetch('Device', id=device_id).configurations = {}
    db.session.commit()
    return True


@post(bp, '/search_configurations', 'View')
def search_configurations():
    text = request.form['search_text']
    regex = 'regular_expression' in request.form
    devices = []
    for device in fetch_all('Device'):
        if not device.configurations:
            continue
        if request.form['config-to-search'] == 'current':
            config = device.configurations[max(device.configurations)]
            if search(text, config) if regex else text in config:
                devices.append(device.serialized)
        elif any(
            search(text, config) if regex else text in config
            for config in device.configurations.values()
        ):
            devices.append(device.serialized)
    return devices


@get(bp, '/get_raw_logs/<device_id>/<version>', 'Edit')
def get_raw_logs(device_id, version):
    device = fetch('Device', id=device_id)
    configurations = {
        str(k): v
        for k, v in device.configurations.items()
    }
    return f'<pre>{configurations.get(version, "")}</pre>'

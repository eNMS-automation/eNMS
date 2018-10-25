from flask import (
    abort,
    current_app as app,
    jsonify,
    redirect,
    render_template,
    request,
    url_for
)
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user
)
from pynetbox import api as netbox_api
from sqlalchemy.orm.exc import NoResultFound
from tacacs_plus.client import TACACSClient
from tacacs_plus.flags import TAC_PLUS_AUTHEN_TYPE_ASCII
from requests import get as http_get

from eNMS import db
from eNMS.admin import blueprint
from eNMS.admin.forms import (
    AddUser,
    CreateAccountForm,
    LoginForm,
    GeographicalParametersForm,
    GottyParametersForm,
    NetboxForm,
    OpenNmsForm,
    SyslogServerForm,
    TacacsServerForm,
)
from eNMS.admin.models import (
    Parameters,
    User,
    TacacsServer
)
from eNMS.base.custom_base import factory
from eNMS.base.helpers import permission_required, fetch, vault_helper
from eNMS.base.properties import pretty_names, user_public_properties
from eNMS.logs.models import SyslogServer
from eNMS.objects.models import Device


@blueprint.route('/user_management')
@login_required
@permission_required('Admin Section')
def users():
    form = AddUser(request.form)
    return render_template(
        'user_management.html',
        fields=user_public_properties,
        names=pretty_names,
        users=User.serialize(),
        form=form
    )


@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = str(request.form['name'])
        user_password = str(request.form['password'])
        user = fetch(User, name=name)
        if user:
            if app.config['USE_VAULT']:
                pwd = vault_helper(app, f'user/{user.name}')['password']
            else:
                pwd = user.password
            if user_password == pwd:
                login_user(user)
                return redirect(url_for('base_blueprint.dashboard'))
        else:
            try:
                # tacacs_plus does not support py2 unicode, hence the
                # conversion to string.
                # TACACSClient cannot be saved directly to session
                # as it is not serializable: this temporary fixes will create
                # a new instance of TACACSClient at each TACACS connection
                # attemp: clearly suboptimal, to be improved later.
                tacacs_server = db.session.query(TacacsServer).one()
                tacacs_client = TACACSClient(
                    str(tacacs_server.ip_address),
                    int(tacacs_server.port),
                    str(tacacs_server.password)
                )
                if tacacs_client.authenticate(
                    name,
                    user_password,
                    TAC_PLUS_AUTHEN_TYPE_ASCII
                ).valid:
                    user = User(name=name, password=user_password)
                    db.session.add(user)
                    db.session.commit()
                    login_user(user)
                    return redirect(url_for('base_blueprint.dashboard'))
            except NoResultFound:
                pass
        return render_template('errors/page_403.html')
    if not current_user.is_authenticated:
        return render_template(
            'login.html',
            login_form=LoginForm(request.form),
            create_account_form=CreateAccountForm(request.form)
        )
    return redirect(url_for('base_blueprint.dashboard'))


@blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin_blueprint.login'))


@blueprint.route('/administration')
@login_required
@permission_required('Admin Section')
def admninistration():
    try:
        tacacs_server = db.session.query(TacacsServer).one()
    except NoResultFound:
        tacacs_server = None
    try:
        syslog_server = db.session.query(SyslogServer).one()
    except NoResultFound:
        syslog_server = None
    return render_template(
        'administration.html',
        geographical_parameters_form=GeographicalParametersForm(request.form),
        gotty_parameters_form=GottyParametersForm(request.form),
        netbox_form=NetboxForm(request.form),
        parameters=db.session.query(Parameters).one(),
        tacacs_form=TacacsServerForm(request.form),
        syslog_form=SyslogServerForm(request.form),
        opennms_form=OpenNmsForm(request.form),
        tacacs_server=tacacs_server,
        syslog_server=syslog_server
    )


@blueprint.route('/create_new_user', methods=['POST'])
def create_new_user():
    user_data = request.form.to_dict()
    if 'permissions' in user_data:
        abort(403)
    return jsonify(factory(User, **user_data).serialized)


@blueprint.route('/process_user', methods=['POST'])
@login_required
@permission_required('Edit Admin Section', redirect=False)
def process_user():
    user_data = request.form.to_dict()
    user_data['permissions'] = request.form.getlist('permissions')
    return jsonify(factory(User, **user_data).serialized)


@blueprint.route('/get/<user_id>', methods=['POST'])
@login_required
@permission_required('Admin Section', redirect=False)
def get_user(user_id):
    user = fetch(User, id=user_id)
    return jsonify(user.serialized)


@blueprint.route('/delete/<user_id>', methods=['POST'])
@login_required
@permission_required('Edit Admin Section', redirect=False)
def delete_user(user_id):
    user = fetch(User, id=user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify(user.serialized)


@blueprint.route('/save_tacacs_server', methods=['POST'])
@login_required
@permission_required('Edit parameters', redirect=False)
def save_tacacs_server():
    TacacsServer.query.delete()
    tacacs_server = TacacsServer(**request.form.to_dict())
    db.session.add(tacacs_server)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/save_syslog_server', methods=['POST'])
@login_required
@permission_required('Edit parameters', redirect=False)
def save_syslog_server():
    SyslogServer.query.delete()
    syslog_server = SyslogServer(**request.form.to_dict())
    db.session.add(syslog_server)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/query_opennms', methods=['POST'])
@login_required
@permission_required('Edit objects', redirect=False)
def query_opennms():
    parameters = db.session.query(Parameters).one()
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
                factory(Device, **devices[device])
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/query_netbox', methods=['POST'])
@login_required
@permission_required('Edit objects', redirect=False)
def query_netbox():
    nb = netbox_api(
        request.form['netbox_address'],
        token=request.form['netbox_token']
    )
    for device in nb.dcim.devices.all():
        device_ip = device.primary_ip4 or device.primary_ip6
        factory(Device, **{
            'name': device.name,
            'ip_address': str(device_ip).split('/')[0],
            'subtype': request.form['netbox_type'],
            'longitude': 0.,
            'latitude': 0.
        })
    return jsonify({'success': True})


@blueprint.route('/save_geographical_parameters', methods=['POST'])
@login_required
@permission_required('Edit parameters', redirect=False)
def save_geographical_parameters():
    parameters = db.session.query(Parameters).one()
    parameters.update(**request.form.to_dict())
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/save_gotty_parameters', methods=['POST'])
@login_required
@permission_required('Edit parameters', redirect=False)
def save_gotty_parameters():
    parameters = db.session.query(Parameters).one()
    parameters.update(**request.form.to_dict())
    db.session.commit()
    return jsonify({'success': True})

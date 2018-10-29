from flask import (
    abort,
    current_app as app,
    jsonify,
    redirect,
    render_template,
    request,
    url_for
)
from flask_login import current_user, login_user, logout_user
from sqlalchemy.orm.exc import NoResultFound
from tacacs_plus.client import TACACSClient
from tacacs_plus.flags import TAC_PLUS_AUTHEN_TYPE_ASCII

from eNMS import db
from eNMS.admin import bp
from eNMS.admin.forms import (
    AddUser,
    CreateAccountForm,
    LoginForm,
    GeographicalParametersForm,
    GottyParametersForm,
    SyslogServerForm,
    TacacsServerForm,
)
from eNMS.base.models import classes
from eNMS.base.helpers import get, post, factory, fetch
from eNMS.base.properties import pretty_names, user_public_properties
from eNMS.base.security import vault_helper
from eNMS.logs.models import SyslogServer


@get(bp, '/user_management', 'Admin Section')
def users():
    form = AddUser(request.form)
    return render_template(
        'user_management.html',
        fields=user_public_properties,
        names=pretty_names,
        users=classes['User'].serialize(),
        form=form
    )


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = str(request.form['name'])
        user_password = str(request.form['password'])
        user = fetch('User', name=name)
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


@get(bp, '/logout')
def logout():
    logout_user()
    return redirect(url_for('admin_blueprint.login'))


@get(bp, '/administration', 'Admin Section')
def admninistration():
    try:
        tacacs_server = db.session.query(classes['TacacsServer']).one()
    except NoResultFound:
        tacacs_server = None
    try:
        syslog_server = db.session.query(classes['SyslogServer']).one()
    except NoResultFound:
        syslog_server = None
    return render_template(
        'administration.html',
        geographical_parameters_form=GeographicalParametersForm(request.form),
        gotty_parameters_form=GottyParametersForm(request.form),
        parameters=db.session.query(Parameters).one(),
        tacacs_form=TacacsServerForm(request.form),
        syslog_form=SyslogServerForm(request.form),
        tacacs_server=tacacs_server,
        syslog_server=syslog_server
    )


@post(bp, '/create_new_user', 'Edit Admin Section')
def create_new_user():
    user_data = request.form.to_dict()
    if 'permissions' in user_data:
        abort(403)
    return jsonify(factory('User', **user_data).serialized)


@post(bp, '/process_user', 'Edit Admin Section')
def process_user():
    user_data = request.form.to_dict()
    user_data['permissions'] = request.form.getlist('permissions')
    return jsonify(factory('User', **user_data).serialized)


@post(bp, '/get/<user_id>', 'Admin Section')
def get_user(user_id):
    return jsonify(fetch('User', id=user_id).serialized)


@post(bp, '/delete/<user_id>', 'Edit Admin Section')
def delete_user(user_id):
    db.session.delete(fetch('User', id=user_id))
    db.session.commit()
    return jsonify(True)


@post(bp, '/save_tacacs_server', 'Edit parameters')
def save_tacacs_server():
    classes['TacacsServer'].query.delete()
    db.session.add(classes['TacacsServer'](**request.form.to_dict()))
    db.session.commit()
    return jsonify(True)


@post(bp, '/save_syslog_server', 'Edit parameters')
def save_syslog_server():
    classes['SyslogServer'].query.delete()
    db.session.add(classes['SyslogServer'](**request.form.to_dict()))
    db.session.commit()
    return jsonify(True)


@post(bp, '/save_geographical_parameters', 'Edit parameters')
def save_geographical_parameters():
    db.session.query(classes['Parameters']).one().update(**request.form.to_dict())
    db.session.commit()
    return jsonify(True)


@post(bp, '/save_gotty_parameters', 'Edit parameters')
def save_gotty_parameters():
    db.session.query(classes['Parameters']).one().update(**request.form.to_dict())
    db.session.commit()
    return jsonify(True)

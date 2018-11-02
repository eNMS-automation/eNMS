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

from eNMS import db
from eNMS.admin import bp
from eNMS.admin.forms import (
    AddUser,
    CreateAccountForm,
    DatabaseFilteringForm,
    GeographicalParametersForm,
    GottyParametersForm,
    LoginForm,
    NotificationParametersForm,
    SyslogServerForm,
    TacacsServerForm,
)
from eNMS.base.models import classes
from eNMS.base.helpers import (
    choices,
    delete,
    get,
    get_one,
    post,
    factory,
    fetch,
    fetch_all,
    serialize
)
from eNMS.base.properties import pretty_names, user_public_properties
from eNMS.base.security import vault_helper


@get(bp, '/user_management', 'Admin Section')
def users():
    return render_template(
        'user_management.html',
        fields=user_public_properties,
        names=pretty_names,
        users=serialize('User'),
        form=AddUser(request.form)
    )


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name, user_password = request.form['name'], request.form['password']
        user = fetch('User', name=name)
        if user:
            if app.config['USE_VAULT']:
                pwd = vault_helper(app, f'user/{user.name}')['password']
            else:
                pwd = user.password
            if user_password == pwd:
                login_user(user)
                return redirect(url_for('base_blueprint.dashboard'))
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
    database_filtering_form = DatabaseFilteringForm(request.form)
    database_filtering_form.pool.choices = choices('Pool')
    try:
        tacacs_server = get_one('TacacsServer')
    except NoResultFound:
        tacacs_server = None
    try:
        syslog_server = get_one('SyslogServer')
    except NoResultFound:
        syslog_server = None
    return render_template(
        'administration.html',
        database_filtering_form=database_filtering_form,
        geographical_parameters_form=GeographicalParametersForm(request.form),
        gotty_parameters_form=GottyParametersForm(request.form),
        notification_parameters_form=NotificationParametersForm(request.form),
        parameters=get_one('Parameters'),
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
    return jsonify(delete('User', id=user_id))


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
    get_one('Parameters').update(**request.form.to_dict())
    db.session.commit()
    return jsonify(True)


@post(bp, '/save_gotty_parameters', 'Edit parameters')
def save_gotty_parameters():
    get_one('Parameters').update(**request.form.to_dict())
    db.session.commit()
    return jsonify(True)


@post(bp, '/save_notification_parameters', 'Edit parameters')
def save_notification_parameters():
    get_one('Parameters').update(**request.form.to_dict())
    db.session.commit()
    return jsonify(True)


@post(bp, '/database_filtering', 'Edit parameters')
def database_filtering():
    pool = fetch('Pool', id=request.form['pool'])
    pool_objects = {'Device': pool.devices, 'Link': pool.links}
    for obj_type in ('Device', 'Link'):
        for obj in fetch_all(obj_type):
            setattr(obj, 'hidden', obj not in pool_objects[obj_type])
    db.session.commit()
    return jsonify(True)

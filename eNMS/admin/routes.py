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
from os import makedirs
from os.path import exists
from tacacs_plus.client import TACACSClient
from tacacs_plus.flags import TAC_PLUS_AUTHEN_TYPE_ASCII as FLAG
from yaml import dump, load

from eNMS import db
from eNMS.admin import bp
from eNMS.admin.forms import (
    AddUser,
    AdministrationForm,
    LoginForm,
    MigrationsForm
)
from eNMS.base.helpers import (
    export,
    get,
    get_one,
    post,
    factory,
    fetch,
    fetch_all,
    serialize
)
from eNMS.base.properties import user_public_properties
from eNMS.base.security import vault_helper


@get(bp, '/user_management', 'View')
def user_management():
    return dict(
        fields=user_public_properties,
        users=serialize('User'),
        form=AddUser(request.form)
    )


@get(bp, '/administration', 'View')
def administration():
    return dict(
        form=AdministrationForm(request.form, 'Parameters'),
        parameters=get_one('Parameters')
    )


@get(bp, '/migrations', 'View')
def migrations():
    return dict(migrations_form=MigrationsForm(request.form, 'Parameters'))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name, password = request.form['name'], request.form['password']
        user = fetch('User', name=name)
        if user:
            if app.config['USE_VAULT']:
                pwd = vault_helper(app, f'user/{user.name}')['password']
            else:
                pwd = user.password
            if password == pwd:
                login_user(user)
                return redirect(url_for('base_blueprint.dashboard'))
            else:
                abort(403)
        elif app.tacacs_client:
            if app.tacacs_client.authenticate(name, password, FLAG).valid:
                user = factory('User', **{'name': name, 'password': password})
                login_user(user)
                return redirect(url_for('base_blueprint.dashboard'))
            else:
                abort(403)
        else:
            abort(403)
    if not current_user.is_authenticated:
        return render_template('login.html', login_form=LoginForm(request.form))
    return redirect(url_for('base_blueprint.dashboard'))


@get(bp, '/logout')
def logout():
    logout_user()
    return redirect(url_for('admin_blueprint.login'))


@post(bp, '/save_parameters', 'Admin')
def save_parameters():
    parameters, data = get_one('Parameters'), request.form.to_dict()
    parameters.update(**data)
    app.tacacs_client = TACACSClient(
        parameters.tacacs_ip_address,
        parameters.tacacs_port,
        parameters.tacacs_password
    )
    pool = fetch('Pool', id=request.form['database_filtering_pool'])
    pool_objects = {'Device': pool.devices, 'Link': pool.links}
    for obj_type in ('Device', 'Link'):
        for obj in fetch_all(obj_type):
            setattr(obj, 'hidden', obj not in pool_objects[obj_type])
    db.session.commit()
    return jsonify(True)


@post(bp, '/migration_export', 'Admin')
def migration_export():
    name = request.form['name']
    for cls_name in request.form.getlist('export'):
        path = app.path / 'migrations' / 'import_export' / name
        if not exists(path):
            makedirs(path)
        with open(path / f'{cls_name}.yaml', 'w') as migration_file:
            dump(export(cls_name), migration_file, default_flow_style=False)
    return jsonify(True)


@post(bp, '/migration_import', 'Admin')
def migration_import():
    name = request.form['name']
    for cls in request.form.getlist('export'):
        path = app.path / 'migrations' / 'import_export' / name / f'{cls}.yaml'
        with open(path, 'r') as migration_file:
            for obj in load(migration_file):
                factory(obj.pop('type') if cls == 'Service' else cls, **obj)
    return jsonify(True)

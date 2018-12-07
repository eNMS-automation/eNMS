from datetime import datetime
from flask import (
    abort,
    current_app as app,
    redirect,
    render_template,
    request,
    url_for
)
from flask_login import current_user, login_user, logout_user
from os import listdir

from eNMS import db, use_tacacs, tacacs_client
from eNMS.admin import bp
from eNMS.admin.forms import (
    AddInstance,
    AddUser,
    AdministrationForm,
    LogsForm,
    LoginForm,
    MigrationsForm
)
from eNMS.admin.helpers import migrate_export, migrate_import
from eNMS.base.helpers import (
    fetch_all,
    get,
    get_one,
    post,
    factory,
    fetch,
    serialize
)
from eNMS.base.properties import (
    instance_public_properties,
    user_public_properties
)
from eNMS.objects.helpers import database_filtering


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
        form=AdministrationForm(request.form),
        parameters=get_one('Parameters').serialized
    )


@get(bp, '/database', 'View')
def database():
    return dict(
        logs_form=LogsForm(request.form),
        migrations_form=MigrationsForm(request.form),
        folders=listdir(app.path / 'migrations')
    )


@get(bp, '/instance_management', 'View')
def instance_management():
    return dict(
        fields=instance_public_properties,
        instances=serialize('Instance'),
        form=AddInstance(request.form)
    )


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name, password = request.form['name'], request.form['password']
        user = fetch('User', name=name)
        if user:
            print(password, user.password)
            if password == user.password:
                login_user(user)
                return redirect(url_for('base_blueprint.dashboard'))
            else:
                abort(403)
        elif use_tacacs:
            if tacacs_client.authenticate(name, password).valid:
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
    get_one('Parameters').update(**request.form)
    database_filtering(fetch('Pool', id=request.form['pool']))
    db.session.commit()
    return True


@post(bp, '/clear_logs', 'Admin')
def clear_logs():
    clear_date = datetime.strptime(
        request.form['clear_logs_date'],
        '%d/%m/%Y %H:%M:%S'
    )
    for job in fetch_all('Job'):
        job.logs = {
            date: log for date, log in job.logs.items()
            if datetime.strptime(date, '%Y-%m-%d-%H:%M:%S.%f') > clear_date
        }
    db.session.commit()
    return True


@post(bp, '/reset_status', 'Admin')
def reset_status():
    for job in fetch_all('Job'):
        job.status = 'Idle'
    db.session.commit()
    return True


@post(bp, '/migration_<direction>', 'Admin')
def migration(direction):
    return {
        'import': migrate_import,
        'export': migrate_export
    }[direction](app.path, request.form)

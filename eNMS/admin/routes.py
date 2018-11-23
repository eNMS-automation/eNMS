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
from tacacs_plus.client import TACACSClient
from tacacs_plus.flags import TAC_PLUS_AUTHEN_TYPE_ASCII as FLAG

from eNMS import db, scheduler
from eNMS.admin import bp
from eNMS.admin.forms import (
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
from eNMS.base.properties import user_public_properties
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


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name, input_password = request.form['name'], request.form['password']
        user = fetch('User', name=name)
        if user:
            if input_password == user.password:
                login_user(user)
                return redirect(url_for('base_blueprint.dashboard'))
            else:
                abort(403)
        elif app.tacacs_client:
            if app.tacacs_client.authenticate(name, input_password, FLAG).valid:
                user = factory(
                    'User',
                    **{'name': name, 'password': input_password}
                )
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
    parameters = get_one('Parameters')
    parameters.update(**request.form)
    app.tacacs_client = TACACSClient(
        parameters.tacacs_ip_address,
        parameters.tacacs_port,
        parameters.tacacs_password
    )
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


@post(bp, '/migration_<direction>', 'Admin')
def migration(direction):
    return {
        'import': migrate_import,
        'export': migrate_export
    }[direction](app.path, request.form)


@post(bp, '/scheduler/<action>', 'Admin')
def scheduler_action(action):
    if action == 'shutdown':
        scheduler.shutdown(wait=False)
    else:
        scheduler.start()
    return True

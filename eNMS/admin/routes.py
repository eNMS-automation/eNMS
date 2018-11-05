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
    AdministrationForm,
    LoginForm,
)
from eNMS.base.classes import classes
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
            else:
                abort(403)
        else:
            abort(403)
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
    return render_template(
        'administration.html',
        form=AdministrationForm(request.form),
        parameters=get_one('Parameters')
    )


@post(bp, '/create_new_user', 'Edit Admin Section')
def create_new_user():
    user_data = request.form.to_dict()
    if 'permissions' in user_data:
        abort(403)
    return jsonify(factory('User', **user_data).serialized)


@post(bp, '/process_user', 'Edit Admin Section')
def process_user():
    return jsonify(factory('User', **request.form).serialized)


@post(bp, '/get/<user_id>', 'Admin Section')
def get_user(user_id):
    return jsonify(fetch('User', id=user_id).serialized)


@post(bp, '/delete/<user_id>', 'Edit Admin Section')
def delete_user(user_id):
    return jsonify(delete('User', id=user_id))


@post(bp, '/save_parameters', 'Edit parameters')
def save_parameters():
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

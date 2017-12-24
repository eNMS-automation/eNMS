from base.routes import _render_template
from flask import Blueprint, current_app, request
from flask_login import login_required
from .forms import *
from .models import User
from .properties import user_search_properties

blueprint = Blueprint(
    'users_blueprint', 
    __name__, 
    url_prefix = '/users', 
    template_folder = 'templates'
    )

@blueprint.route('/overview')
@login_required
def users():
    return _render_template(
        'users_overview.html', 
        fields = user_search_properties, 
        users = User.query.all()
        )
                           
@blueprint.route('/manage_users', methods=['GET', 'POST'])
@login_required
def manage_users():
    add_user_form = AddUser(request.form)
    delete_user_form = DeleteUser(request.form)
    if 'add_user' in request.form:
        user = User(**request.form)
        current_app.database.session.add(user)
    elif 'delete_user' in request.form:
        selection = delete_user_form.data['users']
        current_app.database.session.query(User).filter(User.username.in_(selection))\
        .delete(synchronize_session='fetch')
    if request.method == 'POST':
        current_app.database.session.commit()
    all_users = User.choices()
    delete_user_form.users.choices = all_users
    return _render_template(
        'manage_users.html',
        add_user_form = add_user_form,
        delete_user_form = delete_user_form
        )
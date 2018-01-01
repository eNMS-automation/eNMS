from base.database import db
from ast import literal_eval
from .forms import *
from collections import Counter
from flask import Blueprint, render_template, redirect, request, url_for

from .properties import pretty_names

import flask_login

blueprint = Blueprint(
    'base_blueprint', 
    __name__, 
    url_prefix = '', 
    template_folder = 'templates'
    )

## custom template rendering

# modified template rendering that includes the username as an argument
# it is used by the sidebar as well as the top navigation 
def _render_template(*args, **kwargs):
    try: 
        kwargs['user'] = flask_login.current_user.username
    except AttributeError:
        # 'AnonymousUserMixin' object has no attribute 'username'
        pass
    # add the mapping to pretty names for properties
    kwargs['names'] = pretty_names
    return render_template(*args, **kwargs)

# from .database import db
from main import app
from objects.models import Node, Link
from users.models import User

## root of the site

@blueprint.route('/')
def site_root():
    return redirect(url_for('users_blueprint.login'))

## dashboard

@blueprint.route('/dashboard')
@flask_login.login_required
def dashboard():
    # nodes properties
    node_counters = {
        property: 
            Counter(
                map(
                    lambda o: str(getattr(o, property)), 
                    Node.query.all()
                    )
                )
        for property in literal_eval(flask_login.current_user.dashboard_node_properties)
        }
    # link properties
    link_counters = {
        property: 
            Counter(
                map(
                    lambda o: str(getattr(o, property)), 
                    Link.query.all()
                    )
                )
        for property in literal_eval(flask_login.current_user.dashboard_link_properties)
        }
    # total number of nodes / links / users
    counters = {
    'nodes': len(Node.query.all()),
    'links': len(Link.query.all()),
    'users': len(User.query.all())
    }
    return _render_template(
        'home/dashboard.html', 
        node_counters = node_counters,
        link_counters = link_counters,
        counters = counters
        )

@blueprint.route('/dashboard_control', methods=['GET', 'POST'])
@flask_login.login_required
def dashboard_control():
    diagram_properties_form = DiagramPropertiesForm(request.form)
    if request.method == 'POST':
        user = db.session.query(User)\
        .filter_by(username=flask_login.current_user.username)\
        .first()
        user.dashboard_node_properties = str(diagram_properties_form.data['node_properties'])
        user.dashboard_link_properties = str(diagram_properties_form.data['link_properties'])
        db.session.commit()
    return _render_template(
        'home/dashboard_control.html',
        diagram_properties_form = diagram_properties_form,
        )

@blueprint.route('/project')
@flask_login.login_required
def project():
    return _render_template('about/project.html')
        
## Errors

@app.login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('errors/page_403.html')

@blueprint.errorhandler(403)
def not_found_error(error):
    return render_template('errors/page_403.html'), 403

@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('errors/page_404.html'), 404

@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('errors/page_500.html'), 500

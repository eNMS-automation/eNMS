from collections import Counter
from flask import Blueprint, jsonify, render_template, redirect, url_for
from .properties import pretty_names, reverse_pretty_names

import flask_login

blueprint = Blueprint(
    'base_blueprint',
    __name__,
    url_prefix='',
    template_folder='templates'
)

from objects.models import Node, Link
from .properties import type_to_diagram_properties
from scripts.models import Script
from tasks.models import Task
from users.models import User
from users.routes import login_manager
from workflows.models import Workflow


@blueprint.route('/')
def site_root():
    return redirect(url_for('users_blueprint.login'))


types = {
    'node': Node,
    'link': Link,
    'user': User,
    'script': Script,
    'workflow': Workflow,
    'task': Task
}


@blueprint.route('/dashboard')
@flask_login.login_required
def dashboard():
    return render_template(
        'dashboard/dashboard.html',
        names=pretty_names,
        properties=type_to_diagram_properties,
        default_properties=dict.fromkeys(types, 'type'),
        counters={name: len(cls.query.all()) for name, cls in types.items()}
    )


@blueprint.route('/<property>_<type>', methods=['POST'])
@flask_login.login_required
def get_counters(property, type):
    objects, property = types[type].query.all(), reverse_pretty_names[property]
    return jsonify(Counter(map(lambda o: str(getattr(o, property)), objects)))


@blueprint.route('/project')
@flask_login.login_required
def project():
    return render_template('about/project.html')

## Errors


@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('errors/page_403.html'), 403


@blueprint.errorhandler(403)
def authorization_required(error):
    return render_template('errors/page_403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('errors/page_404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('errors/page_500.html'), 500

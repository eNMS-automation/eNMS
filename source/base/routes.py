from collections import Counter
from flask import (
    Blueprint,
    jsonify,
    render_template,
    redirect,
    request,
    url_for
)
from flask_login import login_required
from .properties import pretty_names, reverse_pretty_names

import flask_login

blueprint = Blueprint(
    'base_blueprint',
    __name__,
    url_prefix='',
    template_folder='templates'
)

from .forms import LogFilteringForm
from .models import Log
from objects.models import Node, Link
from .properties import type_to_diagram_properties
from re import search
from scripts.models import Script
from tasks.models import Task
from admin.models import User
from admin.routes import login_manager
from workflows.models import Workflow

types = {
    'node': Node,
    'link': Link,
    'user': User,
    'script': Script,
    'workflow': Workflow,
    'task': Task
}

## Template rendering


@blueprint.route('/')
def site_root():
    return redirect(url_for('admin_blueprint.login'))


@blueprint.route('/dashboard')
@flask_login.login_required
def dashboard():
    return render_template(
        'template/dashboard.html',
        names=pretty_names,
        properties=type_to_diagram_properties,
        default_properties=dict.fromkeys(types, 'type'),
        counters={name: len(cls.query.all()) for name, cls in types.items()}
    )


@blueprint.route('/logs')
@login_required
def logs():
    form = LogFilteringForm(request.form)
    return render_template(
        'template/logs_overview.html',
        form=form,
        names=pretty_names,
        logs=Log.query.all(),
    )


## AJAX calls


@blueprint.route('/filter_logs', methods=['POST'])
@flask_login.login_required
def filter_logs():
    logs = [log.get_properties() for log in Log.query.all() if all(
        # if the node-regex property is not in the request, the
        # regex box is unticked and we only check that the values
        # are equal.
        str(value) == request.form[property]
        if not property + 'regex' in request.form
        # if it is ticked, we use re.search to check that the value
        # of the node property matches the regular expression.
        else search(request.form[property], str(value))
        for property, value in log.__dict__.items()
        # we consider only the properties in the form
        # providing that the property field in the form is not empty
        # (empty field <==> property ignored)
        if property in request.form and request.form[property]
    )]
    print(logs)
    return jsonify(logs)


@blueprint.route('/<property>_<type>', methods=['POST'])
@flask_login.login_required
def get_counters(property, type):
    objects, property = types[type].query.all(), reverse_pretty_names[property]
    return jsonify(Counter(map(lambda o: str(getattr(o, property)), objects)))


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

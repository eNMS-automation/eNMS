from base.database import db, get_obj
from collections import Counter
from flask import jsonify, render_template, redirect, request, url_for
from flask_login import login_required
from .properties import pretty_names, reverse_pretty_names
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
import flask_login

types = {
    'node': Node,
    'link': Link,
    'user': User,
    'script': Script,
    'workflow': Workflow,
    'task': Task
}

default_properties = {
    'node': 'vendor',
    'link': 'location',
    'user': 'access_rights',
    'script': 'type',
    'workflow': 'vendor',
    'task': 'type'
}

## Template rendering


@blueprint.route('/')
def site_root():
    return redirect(url_for('admin_blueprint.login'))


@blueprint.route('/dashboard')
@flask_login.login_required
def dashboard():
    return render_template(
        'dashboard.html',
        names=pretty_names,
        properties=type_to_diagram_properties,
        default_properties=default_properties,
        counters={name: len(cls.query.all()) for name, cls in types.items()}
    )


@blueprint.route('/logs')
@login_required
def logs():
    form = LogFilteringForm(request.form)
    return render_template(
        'logs_overview.html',
        form=form,
        names=pretty_names,
        fields=('source', 'content'),
        logs=Log.serialize(),
    )


## AJAX calls


@blueprint.route('/filter_logs', methods=['POST'])
@flask_login.login_required
def filter_logs():
    print(Log.serialize())
    logs = [log for log in Log.serialize() if all(
        # if the node-regex property is not in the request, the
        # regex box is unticked and we only check that the values
        # are equal.
        str(val) == request.form[prop] if not prop + 'regex' in request.form
        # if it is ticked, we use re.search to check that the value
        # of the node property matches the regular expression,
        # providing that the property field in the form is not empty
        # (empty field <==> property ignored)
        else search(request.form[prop], str(val)) for prop, val in log.items()
        if prop in request.form and request.form[prop]
    )]
    print(logs)
    return jsonify(logs)


@blueprint.route('/counters/<property>/<type>', methods=['POST'])
@flask_login.login_required
def get_counters(property, type):
    objects = types[type].query.all()
    if property in reverse_pretty_names:
        property = reverse_pretty_names[property]
    return jsonify(Counter(map(lambda o: str(getattr(o, property)), objects)))


@blueprint.route('/delete_log/<log_id>', methods=['POST'])
@login_required
def delete_log(log_id):
    log = get_obj(Log, id=log_id)
    db.session.delete(log)
    db.session.commit()
    return jsonify({})

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

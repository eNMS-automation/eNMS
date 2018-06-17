from collections import Counter
from flask import jsonify, render_template, redirect, request, url_for
from flask_login import login_required
from re import search
import flask_login

from eNMS import db, login_manager
from eNMS.base import blueprint
from eNMS.base.forms import LogFilteringForm
from eNMS.base.classes import diagram_classes
from eNMS.base.models import Log
from eNMS.base.properties import (
    default_diagrams_properties,
    pretty_names,
    reverse_pretty_names,
    type_to_diagram_properties
)
from eNMS.objects.models import get_obj


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
        default_properties=default_diagrams_properties,
        counters={name: len(cls.query.all()) for name, cls in diagram_classes.items()}
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
    return jsonify(logs)


@blueprint.route('/counters/<property>/<type>', methods=['POST'])
@flask_login.login_required
def get_counters(property, type):
    objects = diagram_classes[type].query.all()
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

## Shutdown


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


@blueprint.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

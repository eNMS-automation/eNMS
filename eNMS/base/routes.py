from collections import Counter
from flask import jsonify, render_template, redirect, request, url_for
from flask_login import login_required
from re import search

from eNMS import db
from eNMS.base import blueprint
from eNMS.base.custom_base import factory
from eNMS.base.classes import diagram_classes
from eNMS.base.models import Log
from eNMS.base.properties import (
    default_diagrams_properties,
    pretty_names,
    reverse_pretty_names,
    type_to_diagram_properties
)
from eNMS.base.helpers import permission_required, retrieve


@blueprint.route('/')
def site_root():
    return redirect(url_for('admin_blueprint.login'))


@blueprint.route('/dashboard')
@login_required
def dashboard():
    return render_template(
        'dashboard.html',
        names=pretty_names,
        properties=type_to_diagram_properties,
        default_properties=default_diagrams_properties,
        counters={
            name: len(cls.query.all()) for name, cls in diagram_classes.items()
        }
    )


@blueprint.route('/log_management')
@login_required
def log_management():
    log_filtering_form = LogFilteringForm(request.form)
    return render_template(
        'log_management.html',
        log_filtering_form=log_filtering_form,
        names=pretty_names,
        fields=('source', 'content'),
        logs=Log.serialize()
    )


@blueprint.route('/filter_logs', methods=['POST'])
@login_required
def filter_logs():
    logs = [log for log in Log.serialize() if all(
        # if the regex property is not in the request, the
        # regex box is unticked and we only check that the values of the
        # filters are contained in the values of the log
        request.form[prop] in str(val) if not prop + 'regex' in request.form
        # if it is ticked, we use re.search to check that the value
        # of the device property matches the regular expression,
        # providing that the property field in the form is not empty
        # (empty field <==> property ignored)
        else search(request.form[prop], str(val)) for prop, val in log.items()
        if prop in request.form and request.form[prop]
    )]
    return jsonify(logs)


@blueprint.route('/counters/<property>/<type>', methods=['POST'])
@login_required
def get_counters(property, type):
    objects = diagram_classes[type].query.all()
    if property in reverse_pretty_names:
        property = reverse_pretty_names[property]
    return jsonify(Counter(map(lambda o: str(getattr(o, property)), objects)))


@blueprint.route('/delete_log/<log_id>', methods=['POST'])
@login_required
@permission_required('Edit logs', redirect=False)
def delete_log(log_id):
    log = retrieve(Log, id=log_id)
    db.session.delete(log)
    db.session.commit()
    return jsonify({'success': True})


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


@blueprint.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

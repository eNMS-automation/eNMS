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


@blueprint.route('/counters/<property>/<type>', methods=['POST'])
@login_required
def get_counters(property, type):
    objects = diagram_classes[type].query.all()
    if property in reverse_pretty_names:
        property = reverse_pretty_names[property]
    return jsonify(Counter(map(lambda o: str(getattr(o, property)), objects)))


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


@blueprint.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

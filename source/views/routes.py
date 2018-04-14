from base.database import get_obj
from base.properties import pretty_names, type_to_public_properties
from collections import OrderedDict
from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
    request,
    session,
)
from flask_login import current_user, login_required
from .forms import GoogleEarthForm, SchedulingForm, ViewOptionsForm
from objects.forms import AddNode, AddLink
from objects.models import Filter, Node, node_subtypes, Link
from os.path import join
from passlib.hash import cisco_type7
from scripts.models import Script
from simplekml import Kml
from .styles import create_styles
from subprocess import Popen
from workflows.models import Workflow
# we use os.system and platform.system => namespace conflict
import os
import platform

blueprint = Blueprint(
    'views_blueprint',
    __name__,
    url_prefix='/views',
    template_folder='templates',
    static_folder='static'
)

styles = create_styles(blueprint.root_path)


@blueprint.route('/<view_type>_view', methods=['GET', 'POST'])
@login_required
def view(view_type):
    add_node_form = AddNode(request.form)
    add_link_form = AddLink(request.form)
    view_options_form = ViewOptionsForm(request.form)
    google_earth_form = GoogleEarthForm(request.form)
    scheduling_form = SchedulingForm(request.form)
    scheduling_form.scripts.choices = Script.choices()
    scheduling_form.workflows.choices = Workflow.choices()
    labels = {'node': 'name', 'link': 'name'}
    if 'view_options' in request.form:
        # update labels
        labels = {
            'node': request.form['node_label'],
            'link': request.form['link_label']
        }
    # for the sake of better performances, the view defaults to markercluster
    # if there are more than 2000 nodes
    view = 'leaflet' if len(Node.query.all()) < 2000 else 'markercluster'
    if 'view' in request.form:
        view = request.form['view']
    # we clean the session's selected nodes
    session['selection'] = []
    # name to id
    name_to_id = {node.name: id for id, node in enumerate(Node.query.all())}
    return render_template(
        '{}_view.html'.format(view_type),
        filters=Filter.query.all(),
        view=view,
        scheduling_form=scheduling_form,
        view_options_form=view_options_form,
        google_earth_form=google_earth_form,
        add_node_form=add_node_form,
        add_link_form=add_link_form,
        labels=labels,
        names=pretty_names,
        subtypes=node_subtypes,
        name_to_id=name_to_id,
        node_table={
            obj: OrderedDict([
                (property, getattr(obj, property))
                for property in type_to_public_properties[obj.type]
            ])
            for obj in Node.query.all()
        },
        link_table={
            obj: OrderedDict([
                (property, getattr(obj, property))
                for property in type_to_public_properties[obj.type]
            ])
            for obj in Link.query.all()
        })


@blueprint.route('/connect_to_<name>', methods=['POST'])
@login_required
def putty_connection(name):
    current_os, node = platform.system(), get_obj(Node, name=name)
    password = cisco_type7.decode(current_user.password)
    if current_os == 'Windows':
        path_putty = join(current_app.path_apps, 'putty.exe')
        ssh_connection = '{} -ssh {}@{} -pw {}'.format(
            path_putty,
            current_user.name,
            node.ip_address,
            password
        )
        Popen(ssh_connection.split())
    else:
        arg = "gnome-terminal -e 'bash -c \"sshpass -p {} ssh {}@{}\"'".format(
            password,
            current_user.name,
            node.ip_address
        )
        os.system(arg)
    return jsonify({})


@blueprint.route('/export_to_google_earth', methods=['POST'])
@login_required
def export_to_google_earth():
    kml_file = Kml()
    for node in Node.query.all():
        point = kml_file.newpoint(name=node.name)
        point.coords = [(node.longitude, node.latitude)]
        point.style = styles[node.subtype]
        point.style.labelstyle.scale = request.form['label_size']

    for link in Link.query.all():
        line = kml_file.newlinestring(name=link.name)
        line.coords = [
            (link.source.longitude, link.source.latitude),
            (link.destination.longitude, link.destination.latitude)
        ]
        line.style = styles[link.type]
        line.style.linestyle.width = request.form['line_width']
    filepath = join(current_app.ge_path, request.form['name'] + '.kmz')
    kml_file.save(filepath)
    return jsonify({})


@blueprint.route('/selection', methods=['POST'])
@login_required
def selection():
    session['selection'] = list(set(request.form.getlist('selection[]')))
    return jsonify({})

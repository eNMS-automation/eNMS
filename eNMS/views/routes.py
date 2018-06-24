from flask import current_app, jsonify, render_template, request
from flask_login import current_user, login_required
from os import system as os_system
from os.path import join
from passlib.hash import cisco_type7
from platform import system as platform_system
from simplekml import Kml
from subprocess import Popen

from eNMS.admin.models import Parameters
from eNMS.base.helpers import get_obj
from eNMS.base.models import Log
from eNMS.objects.forms import AddNode, AddLink
from eNMS.objects.models import Pool, Node, node_class, Link
from eNMS.base.properties import (
    link_public_properties,
    node_public_properties,
    pretty_names
)
from eNMS.scripts.models import Script
from eNMS.tasks.forms import SchedulingForm
from eNMS.views import blueprint, styles
from eNMS.views.forms import GoogleEarthForm, ViewOptionsForm


## Template rendering


@blueprint.route('/<view_type>_view', methods=['GET', 'POST'])
@login_required
def view(view_type):
    add_node_form = AddNode(request.form)
    add_link_form = AddLink(request.form)
    all_nodes = Node.choices()
    add_link_form.source.choices = add_link_form.destination.choices = all_nodes
    view_options_form = ViewOptionsForm(request.form)
    google_earth_form = GoogleEarthForm(request.form)
    scheduling_form = SchedulingForm(request.form)
    scheduling_form.scripts.choices = Script.choices()
    scheduling_form.nodes.choices = all_nodes
    scheduling_form.pools.choices = Pool.choices()
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
    # name to id
    name_to_id = {node.name: id for id, node in enumerate(Node.query.all())}
    return render_template(
        '{}_view.html'.format(view_type),
        pools=Pool.query.all(),
        parameters=Parameters.query.one().serialized,
        view=view,
        scheduling_form=scheduling_form,
        view_options_form=view_options_form,
        google_earth_form=google_earth_form,
        add_node_form=add_node_form,
        add_link_form=add_link_form,
        node_fields=node_public_properties,
        link_fields=link_public_properties,
        labels=labels,
        names=pretty_names,
        subtypes=list(node_class),
        name_to_id=name_to_id,
        nodes=Node.serialize(),
        links=Link.serialize()
    )


## AJAX calls


@blueprint.route('/connect_to_<name>', methods=['POST'])
@login_required
def putty_connection(name):
    current_os, node = platform_system(), get_obj(Node, name=name)
    password = cisco_type7.decode(current_user.password)
    if current_os == 'Windows':
        path_putty = join(current_app.path, 'applications', 'putty.exe')
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
        os_system(arg)
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
    filepath = join(current_app.path, 'google_earth', request.form['name'] + '.kmz')
    kml_file.save(filepath)
    return jsonify({})


@blueprint.route('/get_logs_<node_id>', methods=['POST'])
@login_required
def get_logs(node_id):
    node = get_obj(Node, id=node_id)
    node_logs = [l.content for l in Log.query.all() if l.source == node.ip_address]
    return jsonify('\n'.join(node_logs))

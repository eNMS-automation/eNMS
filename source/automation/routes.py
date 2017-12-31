from __future__ import print_function
from base.database import db
from base.routes import _render_template
from flask import Blueprint, current_app, redirect, request, url_for
from flask_login import login_required, current_user
from .forms import *
from objects.models import get_obj, Node, switch_properties
from users.models import User
from scheduling.models import *

blueprint = Blueprint(
    'automation_blueprint', 
    __name__, 
    url_prefix = '/automation', 
    template_folder = 'templates'
    )

@blueprint.route('/netmiko', methods=['GET', 'POST'])
@login_required
def netmiko():
    form = NetmikoForm(request.form)
    # update the list of available nodes by querying the database
    form.nodes.choices = Node.choices()
    if 'send' in request.form or 'create_task' in request.form:
        # if user does not select file, browser also
        # submit a empty part without filename
        filename = request.files['file'].filename
        # retrieve the raw script: we will use it as-is or update it depending
        # on whether a Jinja2 template was uploaded by the user or not
        raw_script = request.form['raw_script']
        if 'file' in request.files and filename:
            if allowed_file(filename, 'netmiko'):
                filename = secure_filename(filename)
                filepath = join(app.config['UPLOAD_FOLDER'], filename)
                with open(filepath, 'r') as f:
                    parameters = load(f)
                template = Template(raw_script)
                script = template.render(**parameters)
            else:
                flash('file {}: format not allowed'.format(filename))
        else:
            script = raw_script
        # we have a list of hostnames, we convert it to a list of IP addresses
        # note: we have to use list of strings as we cannot pass actual objects
        # to an AP Scheduler job.
        node_ips = switch_properties(
            current_app,
            Node,
            form.data['nodes'],
            'name',
            'ip_address'
            )
        netmiko_task = NetmikoTask(script, current_user, node_ips, **form.data)
        db.session.add(netmiko_task)
        db.session.commit()
        return redirect(url_for('scheduling_blueprint.task_management'))
    return _render_template(
        'netmiko.html',
        form = form
        )

@blueprint.route('/napalm_getters', methods=['GET', 'POST'])
@login_required
def napalm_getters():
    form = NapalmGettersForm(request.form)
    # update the list of available users / nodes by querying the database
    form.nodes.choices = Node.choices()
    if 'query' in request.form:
        nodes_info = []
        for name in form.data['nodes']:
            obj = get_obj(current_app, Node, name=name)
            nodes_info.append((obj.ip_address, obj.operating_system.lower()))
        napalm_task = NapalmGettersTask(
            current_user,
            nodes_info,
            **form.data
            )
        db.session.add(napalm_task)
        db.session.commit()
    return _render_template(
        'napalm_getters.html',
        form = form
        )

@blueprint.route('/napalm_configuration', methods=['GET', 'POST'])
@login_required
def napalm_configuration():
    form = NapalmConfigurationForm(request.form)
    # update the list of available users / nodes by querying the database
    form.nodes.choices = Node.choices()
    if 'send' in request.form:
        # if user does not select file, browser also
        # submit a empty part without filename
        filename = request.files['file'].filename
        # retrieve the raw script: we will use it as-is or update it depending
        # on whether a Jinja2 template was uploaded by the user or not
        raw_script = request.form['raw_script']
        if 'file' in request.files and filename:
            if allowed_file(filename, 'netmiko'):
                filename = secure_filename(filename)
                filepath = join(app.config['UPLOAD_FOLDER'], filename)
                with open(filepath, 'r') as f:
                    parameters = load(f)
                template = Template(raw_script)
                script = template.render(**parameters)
            else:
                flash('file {}: format not allowed'.format(filename))
        else:
            script = raw_script
        nodes_info = []
        for name in form.data['nodes']:
            obj = get_obj(current_app, Node, name=name)
            nodes_info.append((obj.ip_address, obj.operating_system.lower()))
        napalm_task = NapalmConfigTask(script, current_user, nodes_info, **form.data)
        db.session.add(napalm_task)
        db.session.commit()
        return redirect(url_for('scheduling_blueprint.task_management'))
    return _render_template(
        'napalm_configuration.html',
        form = form
        )
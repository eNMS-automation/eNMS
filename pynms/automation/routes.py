from __future__ import print_function
from base.routes import _render_template
from flask import Blueprint, current_app, redirect, request, url_for
from flask_login import login_required, current_user
from .forms import *
from objects.models import Node
from users.models import User
from scheduling.models import NetmikoTask

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
        netmiko_task = NetmikoTask(script, current_user, **form.data)
        current_app.database.session.add(netmiko_task)
        current_app.database.session.commit()
        return redirect(url_for('scheduling_blueprint.task_management'))
    return _render_template(
        'netmiko.html',
        form = form
        )

def retrieve_napalm_getters(getters, nodes, *credentials):
    napalm_output = []
    for node in nodes:
        napalm_output.append('\n{}\n'.format(node))
        node_object = current_app.database.session.query(Node)\
            .filter_by(name=node)\
            .first()
        try:
            napalm_node = node_object.napalm_connection(*credentials)
            for getter in getters:
                try:
                    output = str_dict(getattr(napalm_node, getters_mapping[getter])())
                except Exception as e:
                    output = '{} could not be retrieve because of {}'.format(getter, e)
                napalm_output.append(output)
        except Exception as e:
            output = 'could not be retrieve because of {}'.format(e)
            napalm_output.append(output)
    return napalm_output
    
def retrieve_and_store_napalm_getters(getters, nodes, *credentials):
    # create folder with the current timestamp
    current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    folder = join(GETTERS_FOLDER, current_time)
    os.makedirs(folder)
    output = retrieve_napalm_getters(getters, nodes, *credentials)
    with open(join(folder, 'output.txt'), 'w') as f:
        print('\n\n'.join(output), file=f)

@blueprint.route('/napalm_getters', methods=['GET', 'POST'])
@login_required
def napalm_getters():
    form = NapalmGettersForm(request.form)
    # update the list of available users / nodes by querying the database
    form.nodes.choices = Node.choices()
    if 'napalm_query' in request.form:
        selected_nodes = form.data['nodes']
        getters = form.data['getters']
        scheduler_interval = form.data['scheduler']
        napalm_output = retrieve_napalm_getters(
            getters,
            selected_nodes,
            form.data['username'],
            form.data['password'],
            form.data['secret'],
            form.data['protocol'].lower()
            )
        form.output.data = '\n\n'.join(napalm_output)
    return _render_template(
        'napalm_getters.html',
        form = form
        )
                           
def send_napalm_script(script, action, nodes, *credentials):
    napalm_output = []
    for node in nodes:
        node_object = current_app.database.session.query(Node)\
            .filter_by(name=node)\
            .first()
        try:
            napalm_node = node_object.napalm_connection(*credentials)
            if action in ('load_merge_candidate', 'load_replace_candidate'):
                getattr(napalm_node, action)(config=script)
            else:
                getattr(napalm_node, action)()
        except Exception as e:
            output = 'exception {}'.format(e)
            napalm_output.append(output)
    return '\n\n'.join(napalm_output)
                           
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
        selected_nodes = form.data['nodes']
        action = napalm_actions[form.data['actions']]
        scheduler_date = form.data['scheduler']
        form.raw_script.data = send_napalm_script(
            script,
            action,
            selected_nodes,
            form.data['username'],
            form.data['password'],
            form.data['secret'],
            form.data['port'],
            form.data['protocol'].lower()
            )
    return _render_template(
        'napalm_configuration.html',
        form = form
        )
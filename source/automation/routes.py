from __future__ import print_function
from base.database import db
from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    url_for
    )
from flask_login import login_required, current_user
from .forms import *
from .models import Script
from objects.models import get_obj, Node
from users.models import User
from scheduling.models import *

blueprint = Blueprint(
    'automation_blueprint', 
    __name__, 
    url_prefix = '/automation', 
    template_folder = 'templates'
    )

def get_targets(nodes):
    targets = []
    print(nodes)
    for name in nodes:
        print(name)
        obj = get_obj(db, Node, name=name)
        targets.append((
            name,
            obj.ip_address, 
            obj.operating_system.lower()
            ))
    return targets

@blueprint.route('/script_creation', methods=['GET', 'POST'])
@login_required
def script_creation():
    form = ScriptCreationForm(request.form)
    if 'create_script' in request.form:
        # retrieve the raw script: we will use it as-is or update it depending
        # on the type of script (jinja2-enabled template or not)
        content = request.form['text']
        if form.data['type'] != 'simple':
            filename = request.files['file'].filename
            if 'file' in request.files and filename:
                if allowed_file(filename, 'netmiko'):
                    filename = secure_filename(filename)
                    filepath = join(app.config['UPLOAD_FOLDER'], filename)
                    with open(filepath, 'r') as f:
                        parameters = load(f)
                    template = Template(content)
                    content = template.render(**parameters)
                else:
                    flash('file {}: format not allowed'.format(filename))
        print(content)
        script = Script(content, **request.form)
        db.session.add(script)
        db.session.commit()
    return render_template(
        'script_creation.html',
        form = form
        )

@blueprint.route('/netmiko', methods=['GET', 'POST'])
@login_required
def netmiko():
    form = NetmikoForm(request.form)
    # update the list of available nodes / script by querying the database
    form.nodes.choices = Node.choices()
    form.script.choices = Script.choices()
    if 'send' in request.form or 'create_task' in request.form:
        targets = get_targets(form.data['nodes'])
        task = NetmikoTask(current_user, targets, **form.data)
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('scheduling_blueprint.task_management'))
    return render_template(
        'netmiko.html',
        form = form
        )

@blueprint.route('/napalm_getters', methods=['GET', 'POST'])
@login_required
def napalm_getters():
    form = NapalmGettersForm(request.form)
    # update the list of available nodes by querying the database
    form.nodes.choices = Node.choices()
    if 'create_task' in request.form:
        targets = get_targets(form.data['nodes'])
        napalm_task = NapalmGettersTask(
            current_user,
            targets,
            **form.data
            )
        db.session.add(napalm_task)
        db.session.commit()
    return render_template(
        'napalm_getters.html',
        form = form
        )

@blueprint.route('/napalm_configuration', methods=['GET', 'POST'])
@login_required
def napalm_configuration():
    form = NapalmConfigurationForm(request.form)
    # update the list of available nodes / script by querying the database
    form.nodes.choices = Node.choices()
    form.script.choices = Script.choices()
    if 'create_task' in request.form:
        targets = get_targets(form.data['nodes'])
        task = NapalmConfigTask(current_user, targets, **form.data)
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('scheduling_blueprint.task_management'))
    return render_template(
        'napalm_configuration.html',
        form = form
        )
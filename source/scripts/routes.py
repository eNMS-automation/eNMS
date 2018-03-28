from base.database import db
from base.helpers import allowed_file
from base.properties import pretty_names
from flask import Blueprint, current_app, render_template, request
from flask_login import login_required
from .forms import AnsibleScriptForm, ConfigScriptForm, FileTransferScriptForm
from jinja2 import Template
from yaml import load
from scripts.models import (
    AnsibleScript,
    FileTransferScript,
    NapalmConfigScript,
    NapalmGettersScript,
    NetmikoConfigScript,
    Script
)
from os.path import join
from werkzeug import secure_filename

blueprint = Blueprint(
    'scripts_blueprint',
    __name__,
    url_prefix='/scripts',
    template_folder='templates',
    static_folder='static'
)


@blueprint.route('/overview')
@login_required
def scripts():
    return render_template(
        'overview.html',
        fields=('name', 'type'),
        names=pretty_names,
        scripts=Script.query.all()
    )


@blueprint.route('/configuration_script', methods=['GET', 'POST'])
@login_required
def config_script():
    form = ConfigScriptForm(request.form)
    if 'create_script' in request.form:
        # retrieve the raw script: we will use it as-is or update it depending
        # on the type of script (jinja2-enabled template or not)
        content = request.form['text']
        if form.data['type'] != 'simple':
            file = request.files['file']
            filename = secure_filename(file.filename)
            if allowed_file(filename, {'yaml', 'yml'}):
                parameters = load(file.read())
                template = Template(content)
                content = template.render(**parameters)
        script = ConfigScript(content, **request.form)
        db.session.add(script)
        db.session.commit()
    return render_template(
        'configuration_script.html',
        form=form
    )


@blueprint.route('/file_transfer_script', methods=['GET', 'POST'])
@login_required
def file_transfer_script():
    form = FileTransferScriptForm(request.form)
    if request.method == 'POST':
        script = FileTransferScript(**request.form)
        db.session.add(script)
        db.session.commit()
    return render_template(
        'file_transfer_script.html',
        form=form
    )


@blueprint.route('/ansible_script', methods=['GET', 'POST'])
@login_required
def ansible_script():
    form = AnsibleScriptForm(request.form)
    if request.method == 'POST':
        filename = secure_filename(request.files['file'].filename)
        if allowed_file(filename, {'yaml', 'yml'}):
            playbook_path = join(current_app.config['UPLOAD_FOLDER'], filename)
            request.files['file'].save(playbook_path)
        script = AnsibleScript(playbook_path, **request.form)
        db.session.add(script)
        db.session.commit()
    return render_template(
        'ansible_script.html',
        form=form
    )

@blueprint.route('/workflow_creation', methods=['GET', 'POST'])
@login_required
def workflow_creation():
    return render_template(
        'workflow.html',
    )
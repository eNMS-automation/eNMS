from base.database import db
from base.helpers import allowed_file
from base.properties import pretty_names
from flask import Blueprint, current_app, render_template, request
from flask_login import login_required
from .forms import (
    AnsibleScriptForm,
    NapalmConfigScriptForm,
    NapalmGettersForm,
    NetmikoConfigScriptForm,
    FileTransferScriptForm
)
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


@blueprint.route('/<script_type>_configuration', methods=['GET', 'POST'])
@login_required
def configuration(script_type):
    form = {
        'netmiko': NetmikoConfigScriptForm,
        'napalm': NapalmConfigScriptForm
        }[script_type](request.form)
    if 'create_script' in request.form:
        # retrieve the raw script: we will use it as-is or update it depending
        # on the type of script (jinja2-enabled template or not)
        content = request.form['text']
        if form.data['content_type'] != 'simple':
            file = request.files['file']
            filename = secure_filename(file.filename)
            if allowed_file(filename, {'yaml', 'yml'}):
                parameters = load(file.read())
                template = Template(content)
                content = template.render(**parameters)
        script = {
            'netmiko': NetmikoConfigScript,
            'napalm': NapalmConfigScript
            }[script_type](content, **request.form)
        db.session.add(script)
        db.session.commit()
    return render_template(
        script_type + '_configuration.html',
        form=form
    )


@blueprint.route('/getters', methods=['GET', 'POST'])
@login_required
def napalm_getters():
    form = NapalmGettersForm(request.form)
    if 'create_script' in request.form:
        script = NapalmGettersScript(**request.form)
        db.session.add(script)
        db.session.commit()
    return render_template(
        'napalm_getters.html',
        form=form
    )


@blueprint.route('/file_transfer', methods=['GET', 'POST'])
@login_required
def file_transfer_script():
    form = FileTransferScriptForm(request.form)
    if request.method == 'POST':
        script = FileTransferScript(**request.form)
        db.session.add(script)
        db.session.commit()
    return render_template(
        'file_transfer.html',
        form=form
    )


@blueprint.route('/ansible', methods=['GET', 'POST'])
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
        'ansible.html',
        form=form
    )

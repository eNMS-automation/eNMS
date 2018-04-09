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


@blueprint.route('/script_creation', methods=['GET', 'POST'])
@login_required
def configuration():
    netmiko_config_form = NetmikoConfigScriptForm(request.form)
    napalm_config_form = NapalmConfigScriptForm(request.form)
    napalm_getters_form = NapalmGettersForm(request.form)
    file_transfer_form = FileTransferScriptForm(request.form)
    ansible_form = AnsibleScriptForm(request.form)
    if request.method == 'POST':
        script_type = request.form['create_script']
        if script_type in ('netmiko_config', 'napalm_config'):
            form = {
                'netmiko_config': netmiko_config_form,
                'napalm_config': napalm_config_form
            }[script_type]
            # retrieve the raw script: we will use it as-is or update it
            # depending on the type of script (jinja2-enabled template or not)
            content = request.form['text']
            if form.data['content_type'] != 'simple':
                file = request.files['file']
                filename = secure_filename(file.filename)
                if allowed_file(filename, {'yaml', 'yml'}):
                    parameters = load(file.read())
                    template = Template(content)
                    content = template.render(**parameters)
            script = {
                'netmiko_config': NetmikoConfigScript,
                'napalm_config': NapalmConfigScript
            }[script_type](content, **request.form)
        elif script_type == 'ansible_playbook':
            filename = secure_filename(request.files['file'].filename)
            if allowed_file(filename, {'yaml', 'yml'}):
                playbook_path = join(current_app.config['UPLOAD_FOLDER'], filename)
                request.files['file'].save(playbook_path)
            script = AnsibleScript(playbook_path, **request.form)
        else:
            script = {
                'napalm_getters': NapalmGettersScript,
                'file_transfer': FileTransferScript,
            }[script_type](**request.form)
        db.session.add(script)
        db.session.commit()
    return render_template(
        'script_creation.html',
        names=pretty_names,
        netmiko_config_form=netmiko_config_form,
        napalm_config_form=napalm_config_form,
        napalm_getters_form=napalm_getters_form,
        file_transfer_form=file_transfer_form,
        ansible_form=ansible_form
    )

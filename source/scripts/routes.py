from base.database import db, get_obj
from base.helpers import allowed_file
from base.properties import pretty_names
from flask import Blueprint, current_app, jsonify, render_template, request
from flask_login import login_required
from .forms import (
    AnsibleScriptForm,
    NapalmConfigScriptForm,
    NapalmGettersForm,
    NetmikoConfigScriptForm,
    FileTransferScriptForm,
    NetmikoValidationForm
)
from jinja2 import Template
from os.path import join
from .properties import type_to_properties
from .models import (
    AnsibleScript,
    FileTransferScript,
    NapalmConfigScript,
    NapalmGettersScript,
    NetmikoConfigScript,
    NetmikoValidationScript,
    Script,
    script_factory,
    type_to_class
)
from werkzeug import secure_filename
from yaml import load

blueprint = Blueprint(
    'scripts_blueprint',
    __name__,
    url_prefix='/scripts',
    template_folder='templates',
    static_folder='static'
)

## Template rendering

type_to_form = {
    'netmiko_config': NetmikoConfigScriptForm,
    'napalm_config': NapalmConfigScriptForm,
    'napalm_getters': NapalmGettersForm,
    'file_transfer': FileTransferScriptForm,
    'netmiko_validation': NetmikoValidationForm,
    'ansible_playbook': AnsibleScriptForm
}

type_to_name = {
    'netmiko_config': 'Netmiko Config',
    'napalm_config': 'NAPALM Config',
    'napalm_getters': 'NAPALM Getters',
    'file_transfer': 'File Transfer',
    'netmiko_validation': 'Validation',
    'ansible_playbook': 'Ansible playbook'
}


@blueprint.route('/script_management')
@login_required
def scripts():
    return render_template(
        'script_management.html',
        fields=('name', 'type'),
        type_to_form={t: s(request.form) for t, s in type_to_form.items()},
        names=pretty_names,
        scripts=Script.query.all()
    )


@blueprint.route('/script_creation')
@login_required
def configuration():
    return render_template(
        'script_creation.html',
        names=pretty_names,
        type_to_form={t: s(request.form) for t, s in type_to_form.items()},
        type_to_name=type_to_name
    )


## AJAX calls


@blueprint.route('/get_<script_type>_<name>', methods=['POST'])
@login_required
def get_script(script_type, name):
    script = get_obj(Script, name=name)
    properties = type_to_properties[script_type]
    script_properties = {
        property: str(getattr(script, property))
        for property in properties
    }
    return jsonify(script_properties)


@blueprint.route('/script_type_<script_type>', methods=['POST'])
@login_required
def get_script_per_type(script_type):
    return jsonify([s.name for s in type_to_class[script_type].query.all()])


@blueprint.route('/delete_<name>', methods=['POST'])
@login_required
def delete_object(name):
    script = get_obj(Script, name=name)
    db.session.delete(script)
    db.session.commit()
    return jsonify({})


@blueprint.route('/create_script_<script_type>', methods=['POST'])
@login_required
def create_script(script_type):
    properties = request.form.to_dict()
    script = get_obj(Script, name=properties['name'])
    if script:
        print(properties)
        properties['type'] = script_type
        script_factory(**properties)
        db.session.commit()
    elif script_type in ('netmiko_config', 'napalm_config'):
        # retrieve the raw script: we will use it as-is or update it
        # depending on the type of script (jinja2-enabled template or not)
        real_content = request.form['content']
        if request.form['content_type'] != 'simple':
            file = request.files['file']
            filename = secure_filename(file.filename)
            if allowed_file(filename, {'yaml', 'yml'}):
                parameters = load(file.read())
                template = Template(real_content)
                real_content = template.render(**parameters)
        script = {
            'netmiko_config': NetmikoConfigScript,
            'napalm_config': NapalmConfigScript
        }[script_type](real_content, **request.form)
    elif script_type == 'ansible_playbook':
        playbook_name = request.form['playbook_name']
        playbook_path = join(current_app.path_playbooks, playbook_name)
        script = AnsibleScript(playbook_path, **request.form)
    else:
        script = {
            'napalm_getters': NapalmGettersScript,
            'file_transfer': FileTransferScript,
            'netmiko_validation': NetmikoValidationScript
        }[script_type](**request.form)
    db.session.add(script)
    db.session.commit()
    return jsonify({})

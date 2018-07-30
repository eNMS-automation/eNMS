from flask import current_app, jsonify, render_template, request
from flask_login import login_required
from jinja2 import Template
from os.path import join
from werkzeug import secure_filename
from yaml import load as yaml_load

from eNMS import db
from eNMS.base.helpers import get_obj, allowed_file
from eNMS.base.properties import pretty_names, script_public_properties
from eNMS.objects.models import Node, Pool
from eNMS.scripts import blueprint
from eNMS.scripts.helpers import type_to_form, type_to_name
from eNMS.scripts.models import Script, script_factory, type_to_class
from eNMS.scripts.properties import type_to_properties
from eNMS.tasks.forms import SchedulingForm


## Template rendering


@blueprint.route('/script_management')
@login_required
def scripts():
    scheduling_form = SchedulingForm(request.form)
    scheduling_form.nodes.choices = Node.choices()
    scheduling_form.pools.choices = Pool.choices()
    scheduling_form.scripts.choices = Script.choices()
    return render_template(
        'script_management.html',
        fields=script_public_properties,
        type_to_form={t: s(request.form) for t, s in type_to_form.items()},
        names=pretty_names,
        scheduling_form=scheduling_form,
        scripts=Script.serialize()
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


@blueprint.route('/get/<script_type>/<script_id>', methods=['POST'])
@login_required
def get_script(script_type, script_id):
    script = get_obj(Script, id=script_id)
    properties = type_to_properties[script_type]
    script_properties = {
        property: getattr(script, property)
        for property in properties
    }
    return jsonify(script_properties)


@blueprint.route('/script_type_<script_type>', methods=['POST'])
@login_required
def get_script_per_type(script_type):
    return jsonify([{
        'id': s.id,
        'name': s.name
    } for s in type_to_class[script_type].query.all()])


@blueprint.route('/delete_<script_id>', methods=['POST'])
@login_required
def delete_object(script_id):
    script = get_obj(Script, id=script_id)
    db.session.delete(script)
    db.session.commit()
    return jsonify(script.name)


@blueprint.route('/create_script_<script_type>', methods=['POST'])
@login_required
def create_script(script_type):
    script = get_obj(Script, name=request.form['name'])
    # convert ImmutableMultiDict to an actual dictionnary
    form = dict(request.form)
    if not script:
        if script_type in ('netmiko_config', 'napalm_config'):
            if form['content_type'][0] != 'simple':
                file = request.files['file']
                filename = secure_filename(file.filename)
                if allowed_file(filename, {'yaml', 'yml'}):
                    parameters = yaml_load(file.read())
                    template = Template(form['content'][0])
                    form['content'] = [''.join(template.render(**parameters))]
        elif script_type == 'file_transfer':
            source_file_name = form['source_file'][0]
            source_file_path = join(current_app.path, 'file_transfer', source_file_name)
            form['source_file'] = [source_file_path]
    script = script_factory(script_type, **form)
    db.session.add(script)
    db.session.commit()
    return jsonify(script.serialized)

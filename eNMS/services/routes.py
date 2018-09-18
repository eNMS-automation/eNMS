from flask import current_app, jsonify, render_template, request
from flask_login import login_required
from jinja2 import Template
from os.path import join
from werkzeug import secure_filename
from yaml import load as yaml_load

from eNMS import db
from eNMS.base.custom_base import factory
from eNMS.base.helpers import retrieve, allowed_file
from eNMS.base.properties import pretty_names, service_public_properties
from eNMS.objects.models import Device, Pool
from eNMS.services import blueprint
from eNMS.services.custom_service import CustomService, service_classes
from eNMS.services.helpers import type_to_form, type_to_name
from eNMS.services.models import Job, Service, type_to_class
from eNMS.services.properties import type_to_properties
from eNMS.tasks.forms import SchedulingForm


@blueprint.route('/service_management')
@login_required
def services():
    scheduling_form = SchedulingForm(request.form)
    scheduling_form.devices.choices = Device.choices()
    scheduling_form.pools.choices = Pool.choices()
    scheduling_form.job.choices = Job.choices()
    return render_template(
        'service_management.html',
        fields=service_public_properties,
        type_to_form={t: s(request.form) for t, s in type_to_form.items()},
        names=pretty_names,
        scheduling_form=scheduling_form,
        services=Service.serialize()
    )


@blueprint.route('/service_creation')
@login_required
def configuration():
    return render_template(
        'service_creation.html',
        names=pretty_names,
        type_to_form={t: s(request.form) for t, s in type_to_form.items()},
        type_to_name=type_to_name
    )


@blueprint.route('/custom_services')
@login_required
def custom_services():
    return render_template(
        'custom_services.html',
        services_classes=list(service_classes)
    )


@blueprint.route('/get_form/<cls_name>', methods=['POST'])
@login_required
def get_form(cls_name):
    cls = service_classes[cls_name]

    def build_separator(text):
        return (f'''
            <div style="width: 100%; height: 20px; border-bottom: 1px;
            solid black; text-align: center;">
                <span style="font-size: 15px; padding: 0 10px;">
                    {text}
                </span>
            </div>'''
        )

    def build_text_boxes(properties):
        return ''.join(f'''
        <label>{k}</label>
        <div class='form-group'>
            <input class="form-control" id="{k}" type="text" value="{v}">
        </div>''' for k, v in properties.items()
        )

    form = (
        build_separator('Text properties') +
        build_text_boxes(cls.form[str]) +
        build_separator('Integer properties') +
        build_text_boxes(cls.form[int])
    )
    return jsonify({'form': form, 'instances': cls.choices()})


@blueprint.route('/get_form_values/<service_id>', methods=['POST'])
@login_required
def get_form_values(service_id):
    return jsonify(retrieve(Service, id=service_id).serialized)


@blueprint.route('/get/<service_type>/<service_id>', methods=['POST'])
@login_required
def get_service(service_type, service_id):
    service = retrieve(Service, id=service_id)
    properties = type_to_properties[service_type]
    service_properties = {
        property: getattr(service, property)
        for property in properties
    }
    return jsonify(service_properties)


@blueprint.route('/service_type/<service_type>', methods=['POST'])
@login_required
def get_service_per_type(service_type):
    return jsonify([{
        'id': s.id,
        'name': s.name
    } for s in type_to_class[service_type].query.all()])


@blueprint.route('/delete/<service_id>', methods=['POST'])
@login_required
def delete_object(service_id):
    service = retrieve(Service, id=service_id)
    db.session.delete(service)
    db.session.commit()
    return jsonify(service.name)


@blueprint.route('/create_service/<service_type>', methods=['POST'])
@login_required
def create_service(service_type):
    service = retrieve(Service, name=request.form['name'])
    form = dict(request.form.to_dict())
    form['getters'] = request.form.getlist('getters')
    if not service:
        if service_type in ('netmiko_config', 'napalm_config'):
            if form['content_type'] != 'simple':
                file = request.files['file']
                filename = secure_filename(file.filename)
                if allowed_file(filename, {'yaml', 'yml'}):
                    parameters = yaml_load(file.read())
                    template = Template(form['content'])
                    form['content'] = ''.join(template.render(**parameters))
        elif service_type == 'file_transfer':
            source_file_name = form['source_file']
            source_file_path = join(
                current_app.path,
                'file_transfer',
                source_file_name
            )
            form['source_file'] = source_file_path
    return jsonify(factory(type_to_class[service_type], **form).serialized)

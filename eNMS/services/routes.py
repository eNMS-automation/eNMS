from flask import current_app, jsonify, render_template, request
from flask_login import login_required
from jinja2 import Template
from os.path import join
from sqlalchemy import Boolean, Float, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict
from werkzeug import secure_filename
from yaml import load as yaml_load

from eNMS import db
from eNMS.base.custom_base import factory
from eNMS.base.helpers import retrieve, allowed_file
from eNMS.base.properties import (
    pretty_names,
    property_types,
    service_public_properties
)
from eNMS.objects.models import Device, Pool
from eNMS.services import blueprint
from eNMS.services.custom_service import CustomService, service_classes
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
        names=pretty_names,
        scheduling_form=scheduling_form,
        services=Service.serialize()
    )


@blueprint.route('/service_editor')
@login_required
def service_editor():
    return render_template(
        'service_editor.html',
        services_classes=list(service_classes),
        property_types={k: str(v) for k, v in property_types.items()}
    )


@blueprint.route('/get_form/<cls_name>', methods=['POST'])
@login_required
def get_form(cls_name):
    cls = service_classes[cls_name]

    def build_text_box(c):
        return f'''
            <label>{c.key}</label>
            <div class="form-group">
              <input class="form-control" id="{c.key}"
              name="{c.key}"type="text">
            </div>'''

    def build_select_box(c):
        options = ''.join(
            f'<option value="{k}">{v}</option>'
            for k, v in getattr(cls, f'{c.key}_values')
        )
        return f'''
            <label>{c.key}</label>
            <div class="form-group">
              <select class="form-control" 
              id="{c.key}" name="{c.key}"
              {'multiple size="7"' if property_types[c.key] == list else ''}>
              {options}
              </select>
            </div>'''

    def build_boolean_box(c):
        return '<fieldset>' + ''.join(f'''
            <div class="item">
                <input id="{c.key}" name="{c.key}" type="checkbox">
                <label>{c.key}</label>
            </div>'''
        ) + '</fieldset>'

    form = ''
    for col in cls.__table__.columns:
        if col.key in cls.private:
          continue
        if property_types[col.key] == bool:
            form += build_boolean_box(col)
        elif hasattr(cls, f'{col.key}_values'):
            form += build_select_box(col)
        else:
            form += build_text_box(col)

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
    print(service_properties)
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


@blueprint.route('/save_service/<cls_name>', methods=['POST'])
@login_required
def save_service(cls_name):
    form = dict(request.form.to_dict())
    for key in request.form:
        if property_types.get(key, None) == list:
            form[key] = request.form.getlist(key)
    return jsonify(factory(service_classes[cls_name], **form).serialized)

from flask import jsonify, render_template, request
from flask_login import login_required

from eNMS import db
from eNMS.base.custom_base import factory
from eNMS.base.helpers import retrieve
from eNMS.base.properties import (
    pretty_names,
    property_types,
    service_public_properties
)
from eNMS.objects.models import Device, Pool
from eNMS.services import blueprint
from eNMS.services.models import Job, Service, service_classes
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
        property_types={k: str(v) for k, v in property_types.items()},
        services_classes=list(service_classes)
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
            </div>''') + '</fieldset>'

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


@blueprint.route('/get_service/<service_id>', methods=['POST'])
@login_required
def get_service(service_id):
    return jsonify(retrieve(Service, id=service_id).column_values)


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

from flask import jsonify, render_template, request
from flask_login import login_required

from eNMS import db
from eNMS.base.custom_base import factory
from eNMS.base.helpers import permission_required, retrieve
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
@permission_required('Services section')
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
@permission_required('Services section')
def service_editor():
    return render_template(
        'service_editor.html',
        property_types={k: str(v) for k, v in property_types.items()},
        services_classes=list(service_classes)
    )


@blueprint.route('/get_form/<cls_name>', methods=['POST'])
@login_required
@permission_required('Services section', redirect=False)
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
@permission_required('Services section', redirect=False)
def get_service(service_id):
    return jsonify(retrieve(Service, id=service_id).column_values)


@blueprint.route('/delete/<service_id>', methods=['POST'])
@login_required
@permission_required('Edit services', redirect=False)
def delete_object(service_id):
    service = retrieve(Service, id=service_id)
    db.session.delete(service)
    db.session.commit()
    return jsonify(service.serialized)


@blueprint.route('/save_service/<cls_name>', methods=['POST'])
@login_required
@permission_required('Edit services', redirect=False)
def save_service(cls_name):
    form = dict(request.form.to_dict())
    for key in request.form:
        if property_types.get(key, None) == list:
            form[key] = request.form.getlist(key)
    return jsonify(factory(service_classes[cls_name], **form).serialized)


@blueprint.route('/show_logs/<task_id>', methods=['POST'])
@login_required
@permission_required('Tasks section', redirect=False)
def show_logs(task_id):
    return jsonify(dumps(retrieve(Task, id=task_id).logs, indent=4))


@blueprint.route('/get_diff/<task_id>/<v1>/<v2>', methods=['POST'])
@blueprint.route('/get_diff/<task_id>/<v1>/<v2>/<n1>/<n2>', methods=['POST'])
@login_required
@permission_required('Tasks section', redirect=False)
def get_diff(task_id, v1, v2, n1=None, n2=None):
    task = retrieve(Task, id=task_id)
    has_devices = 'devices' in task.logs[v1] and 'devices' in task.logs[v2]
    if has_devices:
        value_n1 = task.logs[v1]['devices'].get(n1, None)
        value_n2 = task.logs[v2]['devices'].get(n2, None)
    if has_devices and value_n1 and value_n2:
        first = str_dict(value_n1).splitlines()
        second = str_dict(value_n2).splitlines()
    else:
        first = str_dict(task.logs[v1]).splitlines()
        second = str_dict(task.logs[v2]).splitlines()
    opcodes = SequenceMatcher(None, first, second).get_opcodes()
    return jsonify({'first': first, 'second': second, 'opcodes': opcodes})


@blueprint.route('/compare_logs/<task_id>', methods=['POST'])
@login_required
@permission_required('Tasks section', redirect=False)
def compare_logs(task_id):
    task = retrieve(Task, id=task_id)
    if task.type == 'WorkflowTask':
        devices = []
    else:
        devices = [device.name for device in task.devices]
    results = {
        'devices': devices,
        'versions': list(task.logs)
    }
    return jsonify(results)

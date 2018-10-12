from datetime import datetime, timedelta
from difflib import SequenceMatcher
from flask import jsonify, render_template, request
from flask_login import login_required
from json import dumps

from eNMS import db, scheduler
from eNMS.base.custom_base import factory
from eNMS.base.helpers import permission_required, retrieve, str_dict
from eNMS.base.properties import (
    pretty_names,
    property_types,
    service_table_properties,
    workflow_table_properties
)
from eNMS.objects.models import Device, Pool
from eNMS.automation import blueprint
from eNMS.automation.forms import (
    AddJobForm,
    CompareLogsForm,
    ServiceForm,
    WorkflowEditorForm,
    WorkflowCreationForm
)
from eNMS.automation.helpers import scheduler_job
from eNMS.automation.models import (
    Job,
    Service,
    service_classes,
    WorkflowEdge,
    Workflow
)
from eNMS.schedule.forms import SchedulingForm


@blueprint.route('/service_management')
@login_required
@permission_required('Services section')
def service_management():
    service_form = ServiceForm(request.form)
    service_form.devices.choices = Device.choices()
    service_form.pools.choices = Pool.choices()
    return render_template(
        'service_management.html',
        compare_logs_form=CompareLogsForm(request.form),
        fields=service_table_properties,
        names=pretty_names,
        property_types={k: str(v) for k, v in property_types.items()},
        service_form=service_form,
        services_classes=list(service_classes),
        services=Service.serialize()
    )


@blueprint.route('/workflow_management')
@login_required
@permission_required('Workflows section')
def workflow_management():
    workflow_creation_form = WorkflowCreationForm(request.form)
    workflow_creation_form.devices.choices = Device.choices()
    workflow_creation_form.pools.choices = Pool.choices()
    return render_template(
        'workflow_management.html',
        compare_logs_form=CompareLogsForm(request.form),
        names=pretty_names,
        fields=workflow_table_properties,
        workflows=Workflow.serialize(),
        workflow_creation_form=workflow_creation_form
    )


@blueprint.route('/workflow_editor/')
@login_required
@permission_required('Workflows section')
def workflow_editor(workflow_id=None):
    add_job_form = AddJobForm(request.form)
    add_job_form.job.choices = Job.choices()
    workflow_editor_form = WorkflowEditorForm(request.form)
    workflow_editor_form.workflow.choices = Workflow.choices()
    workflow = retrieve(Workflow, id=workflow_id)
    service_form = ServiceForm(request.form)
    service_form.devices.choices = Device.choices()
    service_form.pools.choices = Pool.choices()
    return render_template(
        'workflow_editor.html',
        add_job_form=add_job_form,
        workflow_editor_form=workflow_editor_form,
        compare_logs_form=CompareLogsForm(request.form),
        names=pretty_names,
        property_types={k: str(v) for k, v in property_types.items()},
        service_form=service_form,
        services_classes=list(service_classes),
        workflow=workflow.serialized if workflow_id else None
    )


@blueprint.route('/get_service/<id_or_cls>', methods=['POST'])
@login_required
@permission_required('Services section', redirect=False)
def get_service(id_or_cls):
    service = retrieve(Service, id=id_or_cls)
    cls = service_classes[service.type if service else id_or_cls]

    def build_text_box(c):
        return f'''
            <label>{c.key}</label>
            <div class="form-group">
              <input class="form-control" id="{c.key}"
              name="{c.key}" type="text">
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
    return jsonify({
        'form': form,
        'service': service.column_values if service else None
    })


@blueprint.route('/delete/<service_id>', methods=['POST'])
@login_required
@permission_required('Edit services', redirect=False)
def delete_object(service_id):
    service = retrieve(Service, id=service_id)
    db.session.delete(service)
    db.session.commit()
    return jsonify(service.serialized)


@blueprint.route('/run_job/<job_id>', methods=['POST'])
@login_required
@permission_required('Service section', redirect=False)
def run_job(job_id):
    job = retrieve(Job, id=job_id)
    now = datetime.now() + timedelta(seconds=5)
    scheduler.add_job(
        id=str(now),
        func=scheduler_job,
        run_date=now,
        args=[job_id],
        trigger='date'
    )
    return jsonify(job.serialized)


@blueprint.route('/save_service/<cls_name>', methods=['POST'])
@login_required
@permission_required('Edit services', redirect=False)
def save_service(cls_name):
    form = dict(request.form.to_dict())
    form['devices'] = [
        retrieve(Device, id=id) for id in request.form.getlist('devices')
    ]
    form['pools'] = [
        retrieve(Pool, id=id) for id in request.form.getlist('pools')
    ]
    for key in request.form:
        if property_types.get(key, None) == list:
            form[key] = request.form.getlist(key)
    return jsonify(factory(service_classes[cls_name], **form).serialized)


@blueprint.route('/show_logs/<job_id>', methods=['POST'])
@login_required
@permission_required('Service section', redirect=False)
def show_logs(job_id):
    return jsonify(dumps(retrieve(Job, id=job_id).logs, indent=4))


@blueprint.route('/get_diff/<job_id>/<v1>/<v2>', methods=['POST'])
@login_required
@permission_required('Service section', redirect=False)
def get_diff(job_id, v1, v2, n1=None, n2=None):
    job = retrieve(Job, id=job_id)
    first = str_dict(job.logs[v1]).splitlines()
    second = str_dict(job.logs[v2]).splitlines()
    opcodes = SequenceMatcher(None, first, second).get_opcodes()
    return jsonify({'first': first, 'second': second, 'opcodes': opcodes})


@blueprint.route('/compare_logs/<job_id>', methods=['POST'])
@login_required
@permission_required('Services section', redirect=False)
def compare_logs(job_id):
    job = retrieve(Job, id=job_id)
    results = {
        'versions': list(job.logs)
    }
    return jsonify(results)


@blueprint.route('/add_to_workflow/<workflow_id>', methods=['POST'])
@login_required
@permission_required('Edit workflows', redirect=False)
def add_to_workflow(workflow_id):
    workflow = retrieve(Workflow, id=workflow_id)
    job = retrieve(Job, id=request.form['job'])
    job.workflows.append(workflow)
    db.session.commit()
    return jsonify(job.serialized)


@blueprint.route('/get/<workflow_id>', methods=['POST'])
@login_required
@permission_required('Workflows section', redirect=False)
def get_workflow(workflow_id):
    workflow = retrieve(Workflow, id=workflow_id)
    return jsonify(workflow.serialized if workflow else {})


@blueprint.route('/edit_workflow', methods=['POST'])
@login_required
@permission_required('Edit workflows', redirect=False)
def edit_workflow():
    form = dict(request.form.to_dict())
    form['devices'] = [
        retrieve(Device, id=id) for id in request.form.getlist('devices')
    ]
    form['pools'] = [
        retrieve(Pool, id=id) for id in request.form.getlist('pools')
    ]
    return jsonify(factory(Workflow, **form).serialized)


@blueprint.route('/delete/<workflow_id>', methods=['POST'])
@login_required
@permission_required('Edit workflows', redirect=False)
def delete_workflow(workflow_id):
    workflow = retrieve(Workflow, id=workflow_id)
    db.session.delete(workflow)
    db.session.commit()
    return jsonify(workflow)


@blueprint.route('/add_node/<workflow_id>/<job_id>', methods=['POST'])
@login_required
@permission_required('Edit workflows', redirect=False)
def add_node(workflow_id, job_id):
    workflow = retrieve(Workflow, id=workflow_id)
    job = retrieve(Job, id=job_id)
    workflow.jobs.append(job)
    db.session.commit()
    return jsonify(job.serialized)


@blueprint.route('/delete_node/<workflow_id>/<job_id>', methods=['POST'])
@login_required
@permission_required('Edit workflows', redirect=False)
def delete_node(workflow_id, job_id):
    job = retrieve(Job, id=job_id)
    db.session.delete(job)
    db.session.commit()
    return jsonify(job.properties)


@blueprint.route('/add_edge/<wf_id>/<type>/<source>/<dest>', methods=['POST'])
@login_required
@permission_required('Edit workflows', redirect=False)
def add_edge(wf_id, type, source, dest):
    source_job = retrieve(Job, id=source)
    destination_job = retrieve(Job, id=dest)
    workflow_edge = factory(WorkflowEdge, **{
        'name': f'{source_job.name} -> {destination_job.name}',
        'workflow': retrieve(Workflow, id=wf_id),
        'type': type == 'true',
        'source': source_job,
        'destination': destination_job
    })
    return jsonify(workflow_edge.serialized)


@blueprint.route('/delete_edge/<workflow_id>/<edge_id>', methods=['POST'])
@login_required
@permission_required('Edit workflows', redirect=False)
def delete_edge(workflow_id, edge_id):
    edge = retrieve(WorkflowEdge, id=edge_id)
    db.session.delete(edge)
    db.session.commit()
    return jsonify(edge.properties)


@blueprint.route('/set_as_start/<workflow_id>/<job_id>', methods=['POST'])
@login_required
@permission_required('Edit workflows', redirect=False)
def set_as_start(workflow_id, job_id):
    workflow = retrieve(Workflow, id=workflow_id)
    workflow.start_job = retrieve(Job, id=job_id)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/set_as_end/<workflow_id>/<job_id>', methods=['POST'])
@login_required
@permission_required('Edit workflows', redirect=False)
def set_as_end(workflow_id, job_id):
    workflow = retrieve(Workflow, id=workflow_id)
    workflow.end_job = retrieve(Job, id=job_id)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/save_positions/<workflow_id>', methods=['POST'])
@login_required
@permission_required('Edit workflows', redirect=False)
def save_positions(workflow_id):
    workflow = retrieve(Workflow, id=workflow_id)
    for job_id, position in request.json.items():
        job = retrieve(Job, id=job_id)
        job.positions[workflow.name] = (position['x'], position['y'])
    db.session.commit()
    return jsonify({'success': True})

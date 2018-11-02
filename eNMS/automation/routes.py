from datetime import datetime, timedelta
from difflib import SequenceMatcher
from flask import jsonify, render_template, request, session
from json import dumps

from eNMS import db, scheduler
from eNMS.base.models import service_classes
from eNMS.base.helpers import (
    choices,
    delete,
    factory,
    fetch,
    get,
    objectify,
    post,
    str_dict,
    serialize
)
from eNMS.base.properties import (
    boolean_properties,
    pretty_names,
    property_types,
    service_table_properties,
    workflow_table_properties
)
from eNMS.automation import bp
from eNMS.automation.forms import (
    AddJobForm,
    CompareLogsForm,
    JobForm,
    WorkflowBuilderForm,
    WorkflowForm
)
from eNMS.automation.helpers import scheduler_job


@get(bp, '/service_management', 'Automation Section')
def service_management():
    service_form = JobForm(request.form)
    service_form.devices.choices = choices('Device')
    service_form.pools.choices = choices('Pool')
    return render_template(
        'service_management.html',
        compare_logs_form=CompareLogsForm(request.form),
        fields=service_table_properties,
        names=pretty_names,
        property_types={k: str(v) for k, v in property_types.items()},
        service_form=service_form,
        services_classes=list(service_classes),
        services=serialize('Service')
    )


@get(bp, '/workflow_management', 'Automation Section')
def workflow_management():
    workflow_creation_form = WorkflowForm(request.form)
    workflow_creation_form.devices.choices = choices('Device')
    workflow_creation_form.pools.choices = choices('Pool')
    return render_template(
        'workflow_management.html',
        compare_logs_form=CompareLogsForm(request.form),
        names=pretty_names,
        fields=workflow_table_properties,
        property_types={k: str(v) for k, v in property_types.items()},
        workflows=serialize('Workflow'),
        workflow_creation_form=workflow_creation_form
    )


@get(bp, '/workflow_builder', 'Automation Section')
def workflow_builder():
    add_job_form = AddJobForm(request.form)
    add_job_form.job.choices = choices('Job')
    workflow_builder_form = WorkflowBuilderForm(request.form)
    workflow_builder_form.workflow.choices = choices('Workflow')
    service_form = JobForm(request.form)
    service_form.devices.choices = choices('Device')
    service_form.pools.choices = choices('Pool')
    workflow = fetch('Workflow', id=session.get('workflow', None))
    return render_template(
        'workflow_builder.html',
        workflow=workflow.serialized if workflow else None,
        add_job_form=add_job_form,
        workflow_builder_form=workflow_builder_form,
        compare_logs_form=CompareLogsForm(request.form),
        names=pretty_names,
        property_types={k: str(v) for k, v in property_types.items()},
        service_form=service_form,
        services_classes=list(service_classes)
    )


@post(bp, '/get_service/<id_or_cls>', 'Automation Section')
def get_service(id_or_cls):
    service = fetch('Service', id=id_or_cls)
    cls = service_classes[service.type if service else id_or_cls]

    def build_text_box(c):
        return f'''
            <label>{c.key}</label>
            <div class="form-group">
              <input class="form-control" id="{c.key}"
              name="{c.key}" type="text">
            </div>'''

    def build_textarea_box(c):
        return f'''
            <label>{c.key}</label>
            <div class="form-group">
              <textarea style="height: 150px;" rows="30"
              class="form-control" id="{c.key}"
              name="{c.key}"></textarea>
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
        return '<fieldset>' + f'''
            <div class="item">
                <input id="{c.key}" name="{c.key}" type="checkbox">
                <label>{c.key}</label>
            </div>''' + '</fieldset>'

    form = ''
    for col in cls.__table__.columns:
        if col.key in cls.private:
            continue
        if property_types[col.key] == bool:
            form += build_boolean_box(col)
        elif hasattr(cls, f'{col.key}_values'):
            form += build_select_box(col)
        elif hasattr(cls, f'{col.key}_textarea'):
            form += build_textarea_box(col)
        else:
            form += build_text_box(col)
    return jsonify({
        'form': form,
        'service': service.column_values if service else None
    })


@post(bp, '/get_states/<cls>', 'Automation Section')
def get_states(cls):
    return jsonify([s['state'] for s in serialize(cls.capitalize())])


@post(bp, '/delete/<service_id>', 'Edit Automation Section')
def delete_object(service_id):
    return jsonify(delete('Service', id=service_id))


@post(bp, '/run_job/<job_id>', 'Edit Automation Section')
def run_job(job_id):
    job = fetch('Job', id=job_id)
    now = datetime.now() + timedelta(seconds=5)
    scheduler.add_job(
        id=str(now),
        func=scheduler_job,
        run_date=now,
        args=[job_id],
        trigger='date'
    )
    return jsonify(job.serialized)


@post(bp, '/save_service/<cls_name>', 'Edit Automation Section')
def save_service(cls_name):
    form = dict(request.form.to_dict())
    form['devices'] = objectify('Device', request.form.getlist('devices'))
    form['pools'] = objectify('Pool', request.form.getlist('pools'))
    for key in request.form:
        if property_types.get(key, None) == list:
            form[key] = request.form.getlist(key)
    for property in boolean_properties:
        if property not in form:
            form[property] = 'off'
    return jsonify(factory(cls_name, **form).serialized)


@post(bp, '/show_logs/<job_id>', 'Automation Section')
def show_logs(job_id):
    return jsonify(dumps(fetch('Job', id=job_id).logs, indent=4))


@post(bp, '/get_diff/<job_id>/<v1>/<v2>', 'Automation Section')
def get_diff(job_id, v1, v2, n1=None, n2=None):
    job = fetch('Job', id=job_id)
    first = str_dict(job.logs[v1]).splitlines()
    second = str_dict(job.logs[v2]).splitlines()
    opcodes = SequenceMatcher(None, first, second).get_opcodes()
    return jsonify({'first': first, 'second': second, 'opcodes': opcodes})


@post(bp, '/clear_logs/<job_id>', 'Edit Automation Section')
def clear_logs(job_id):
    fetch('Job', id=job_id).logs = {}
    db.session.commit()
    return jsonify(True)


@post(bp, '/compare_logs/<job_id>', 'Automation Section')
def compare_logs(job_id):
    job = fetch('Job', id=job_id)
    results = {'versions': list(job.logs)}
    return jsonify(results)


@post(bp, '/add_to_workflow/<workflow_id>', 'Edit Automation Section')
def add_to_workflow(workflow_id):
    workflow = fetch('Workflow', id=workflow_id)
    job = fetch('Job', id=request.form['job'])
    job.workflows.append(workflow)
    db.session.commit()
    return jsonify(job.serialized)


@post(bp, '/get/<workflow_id>', 'Automation Section')
def get_workflow(workflow_id):
    workflow = fetch('Workflow', id=workflow_id)
    return jsonify(workflow.serialized if workflow else {})


@post(bp, '/reset_workflow_logs/<workflow_id>', 'Edit Automation Section')
def reset_workflow_logs(workflow_id):
    fetch('Workflow', id=workflow_id).status = {'state': 'Idle'}
    db.session.commit()
    return jsonify(True)


@post(bp, '/edit_workflow', 'Edit Automation Section')
def edit_workflow():
    form = dict(request.form.to_dict())
    for property in boolean_properties:
        if property not in form:
            form[property] = 'off'
    form['devices'] = objectify('Device', request.form.getlist('devices'))
    form['pools'] = objectify('Pool', request.form.getlist('pools'))
    return jsonify(factory('Workflow', **form).serialized)


@post(bp, '/delete_workflow/<workflow_id>', 'Edit Automation Section')
def delete_workflow(workflow_id):
    return jsonify(delete('Workflow', id=workflow_id))


@post(bp, '/add_node/<workflow_id>/<job_id>', 'Edit Automation Section')
def add_node(workflow_id, job_id):
    workflow, job = fetch('Workflow', id=workflow_id), fetch('Job', id=job_id)
    workflow.jobs.append(job)
    db.session.commit()
    return jsonify(job.serialized)


@post(bp, '/delete_node/<workflow_id>/<job_id>', 'Edit Automation Section')
def delete_node(workflow_id, job_id):
    workflow, job = fetch('Workflow', id=workflow_id), fetch('Job', id=job_id)
    workflow.jobs.remove(job)
    db.session.commit()
    return jsonify(job.properties)


@post(bp, '/add_edge/<wf_id>/<type>/<source>/<dest>', 'Edit Automation Section')
def add_edge(wf_id, type, source, dest):
    workflow_edge = factory('WorkflowEdge', **{
        'name': f'{wf_id}-{type}:{source}->{dest}',
        'workflow': fetch('Workflow', id=wf_id),
        'type': type == 'true',
        'source': fetch('Job', id=source),
        'destination': fetch('Job', id=dest)
    })
    return jsonify(workflow_edge.serialized)


@post(bp, '/delete_edge/<workflow_id>/<edge_id>', 'Edit Automation Section')
def delete_edge(workflow_id, edge_id):
    return jsonify(delete('WorkflowEdge', id=edge_id))


@post(bp, '/save_positions/<workflow_id>', 'Edit Automation Section')
def save_positions(workflow_id):
    workflow = fetch('Workflow', id=workflow_id)
    session['workflow'] = workflow.id
    for job_id, position in request.json.items():
        job = fetch('Job', id=job_id)
        job.positions[workflow.name] = (position['x'], position['y'])
    db.session.commit()
    return jsonify(True)

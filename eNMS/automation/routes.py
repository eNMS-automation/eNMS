from datetime import datetime, timedelta
from difflib import SequenceMatcher
from flask import jsonify, request, session
from json import dumps
from logging import info

from eNMS import db, scheduler
from eNMS.base.classes import service_classes
from eNMS.base.helpers import (
    delete,
    factory,
    fetch,
    get,
    post,
    str_dict,
    serialize
)
from eNMS.base.properties import (
    cls_to_properties,
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


@get(bp, '/service_management', 'View')
def service_management():
    return dict(
        compare_logs_form=CompareLogsForm(request.form),
        fields=service_table_properties,
        service_form=JobForm(request.form, 'Service'),
        services_classes=list(service_classes),
        services=serialize('Service')
    )


@get(bp, '/workflow_management', 'View')
def workflow_management():
    return dict(
        compare_logs_form=CompareLogsForm(request.form),
        fields=workflow_table_properties,
        workflows=serialize('Workflow'),
        workflow_creation_form=WorkflowForm(request.form, 'Workflow')
    )


@get(bp, '/workflow_builder', 'View')
def workflow_builder():
    workflow = fetch('Workflow', id=session.get('workflow', None))
    return dict(
        workflow=workflow.serialized if workflow else None,
        add_job_form=AddJobForm(request.form, 'Workflow'),
        workflow_builder_form=WorkflowBuilderForm(request.form, 'Service'),
        workflow_creation_form=WorkflowForm(request.form, 'Workflow'),
        compare_logs_form=CompareLogsForm(request.form),
        service_form=JobForm(request.form, 'Service'),
        services_classes=list(service_classes)
    )


@get(bp, '/logs/<id>/<runtime>', 'View')
def logs(id, runtime):
    message = fetch("Job", id=id).logs.get(runtime, 'Logs have been removed')
    return f'<pre>{dumps(message, indent=4)}</pre>'


@post(bp, '/get_service/<id_or_cls>', 'View')
def get_service(id_or_cls):
    service = fetch('Service', id=id_or_cls)
    cls = service_classes[service.type if service else id_or_cls]

    def build_text_box(property):
        return f'''
            <label>{property}</label>
            <div class="form-group">
              <input class="form-control" id="service-{property}"
              name="{property}" type="text">
            </div>'''

    def build_textarea_box(property):
        return f'''
            <label>{property}</label>
            <div class="form-group">
              <textarea style="height: 150px;" rows="30"
              class="form-control" id="service-{property}"
              name="{property}"></textarea>
            </div>'''

    def build_select_box(property):
        options = ''.join(
            f'<option value="{k}">{v}</option>'
            for k, v in getattr(cls, f'{property}_values')
        )
        return f'''
            <label>{property}</label>
            <div class="form-group">
              <select class="form-control"
                id="service-{property}" name="{property}"
                {'multiple size="7"'
                if property_types[property] == 'list'
                else ''}>{options}
              </select>
            </div>'''

    def build_boolean_box(property):
        return '<fieldset>' + f'''
            <div class="item">
                <input id="service-{property}" name="{property}"
                type="checkbox"><label>{property}</label>
            </div>''' + '</fieldset>'

    form = ''
    for property in cls_to_properties[cls.__tablename__]:
        if property in cls_to_properties['Service']:
            continue
        if property_types.get(property, None) == 'bool':
            form += build_boolean_box(property)
        elif hasattr(cls, f'{property}_values'):
            form += build_select_box(property)
        elif hasattr(cls, f'{property}_textarea'):
            form += build_textarea_box(property)
        else:
            form += build_text_box(property)
    return jsonify({
        'form': form,
        'service': service.serialized if service else None
    })


@post(bp, '/get_status/<cls>', 'View')
def get_status(cls):
    return jsonify([s['status'] for s in serialize(cls.capitalize())])


@post(bp, '/run_job/<job_id>', 'Edit')
def run_job(job_id):
    job = fetch('Job', id=job_id)
    if job.status == 'Running':
        return jsonify({'error': 'Job is already running.'})
    job.status, job.state = 'Running', {}
    info(f'{job.name}: starting.')
    db.session.commit()
    now = datetime.now() + timedelta(seconds=5)
    scheduler.add_job(
        id=str(now),
        func=scheduler_job,
        run_date=now,
        args=[job_id],
        trigger='date'
    )
    return jsonify(job.serialized)


@post(bp, '/get_diff/<job_id>/<v1>/<v2>', 'View')
def get_diff(job_id, v1, v2, n1=None, n2=None):
    job = fetch('Job', id=job_id)
    first = str_dict(job.logs[v1]).splitlines()
    second = str_dict(job.logs[v2]).splitlines()
    opcodes = SequenceMatcher(None, first, second).get_opcodes()
    return jsonify({'first': first, 'second': second, 'opcodes': opcodes})


@post(bp, '/clear_logs/<job_id>', 'Edit')
def clear_logs(job_id):
    fetch('Job', id=job_id).logs = {}
    db.session.commit()
    return jsonify(True)


@post(bp, '/add_to_workflow/<workflow_id>', 'Edit')
def add_to_workflow(workflow_id):
    workflow = fetch('Workflow', id=workflow_id)
    job = fetch('Job', id=request.form['job'])
    job.workflows.append(workflow)
    db.session.commit()
    return jsonify(job.serialized)


@post(bp, '/duplicate_workflow/<workflow_id>', 'Edit')
def duplicate_workflow(workflow_id):
    parent_workflow = fetch('Workflow', id=workflow_id)
    new_workflow = factory('Workflow', **request.form)
    for job in parent_workflow.jobs:
        new_workflow.jobs.append(job)
        job.positions[new_workflow.name] = job.positions[parent_workflow.name]
    for edge in parent_workflow.edges:
        subtype, src, dest = edge.subtype, edge.source, edge.destination
        new_workflow.edges.append(factory('WorkflowEdge', **{
            'name': f'{new_workflow.id}-{subtype}:{src.id}->{dest.id}',
            'workflow': new_workflow.id,
            'subtype': subtype,
            'source': src.id,
            'destination': dest.id
        }))
    db.session.commit()
    return jsonify(new_workflow.serialized)


@post(bp, '/reset_workflow_logs/<workflow_id>', 'Edit')
def reset_workflow_logs(workflow_id):
    fetch('Workflow', id=workflow_id).state = {}
    db.session.commit()
    return jsonify(True)


@post(bp, '/add_node/<workflow_id>/<job_id>', 'Edit')
def add_node(workflow_id, job_id):
    workflow, job = fetch('Workflow', id=workflow_id), fetch('Job', id=job_id)
    workflow.jobs.append(job)
    db.session.commit()
    return jsonify(job.serialized)


@post(bp, '/delete_node/<workflow_id>/<job_id>', 'Edit')
def delete_node(workflow_id, job_id):
    workflow, job = fetch('Workflow', id=workflow_id), fetch('Job', id=job_id)
    workflow.jobs.remove(job)
    db.session.commit()
    return jsonify(job.serialized)


@post(bp, '/add_edge/<wf_id>/<subtype>/<source>/<dest>', 'Edit')
def add_edge(wf_id, subtype, source, dest):
    workflow_edge = factory('WorkflowEdge', **{
        'name': f'{wf_id}-{subtype}:{source}->{dest}',
        'workflow': wf_id,
        'subtype': subtype == 'true',
        'source': source,
        'destination': dest
    })
    return jsonify(workflow_edge.serialized)


@post(bp, '/delete_edge/<workflow_id>/<edge_id>', 'Edit')
def delete_edge(workflow_id, edge_id):
    return jsonify(delete('WorkflowEdge', id=edge_id))


@post(bp, '/save_positions/<workflow_id>', 'Edit')
def save_positions(workflow_id):
    workflow = fetch('Workflow', id=workflow_id)
    session['workflow'] = workflow.id
    for job_id, position in request.json.items():
        job = fetch('Job', id=job_id)
        job.positions[workflow.name] = (position['x'], position['y'])
    db.session.commit()
    return jsonify(True)

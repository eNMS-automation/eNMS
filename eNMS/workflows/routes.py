from flask import jsonify, render_template, request
from flask_login import login_required

from eNMS import db
from eNMS.base.custom_base import factory
from eNMS.base.helpers import permission_required, retrieve
from eNMS.base.properties import pretty_names, workflow_table_properties
from eNMS.objects.models import Device, Pool
from eNMS.services.forms import CompareLogsForm
from eNMS.services.models import Job
from eNMS.tasks.models import Task
from eNMS.tasks.forms import SchedulingForm
from eNMS.workflows import blueprint
from eNMS.workflows.forms import (
    AddExistingTaskForm,
    WorkflowEditorForm,
    WorkflowCreationForm
)
from eNMS.workflows.models import WorkflowEdge, Workflow


@blueprint.route('/workflow_management')
@login_required
@permission_required('Workflows section')
def workflows():
    scheduling_form = SchedulingForm(request.form)
    scheduling_form.job.choices = Job.choices()
    return render_template(
        'workflow_management.html',
        compare_logs_form=CompareLogsForm(request.form),
        names=pretty_names,
        scheduling_form=scheduling_form,
        fields=workflow_table_properties,
        workflows=Workflow.serialize(),
        form=WorkflowCreationForm(request.form)
    )


@blueprint.route('/workflow_editor/')
@login_required
@permission_required('Workflows section')
def workflow_editor(workflow_id=None):
    add_job_form = AddJobForm(request.form)
    workflow_editor_form = WorkflowEditorForm(request.form)
    workflow_editor_form.workflow.choices = Workflow.choices()
    workflow = retrieve(Workflow, id=workflow_id)
    scheduling_form = SchedulingForm(request.form)
    scheduling_form.job.choices = Job.choices()
    add_job_form.job.choices = Job.choices()
    return render_template(
        'workflow_editor.html',
        add_job_form=add_job_form,
        workflow_editor_form=workflow_editor_form,
        scheduling_form=scheduling_form,
        compare_logs_form=CompareLogsForm(request.form),
        names=pretty_names,
        workflow=workflow.serialized if workflow_id else None
    )


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
    return jsonify(factory(Workflow, **request.form.to_dict()).serialized)


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
    workflow.start_job = job_id
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/set_as_end/<workflow_id>/<job_id>', methods=['POST'])
@login_required
@permission_required('Edit workflows', redirect=False)
def set_as_end(workflow_id, job_id):
    workflow = retrieve(Workflow, id=workflow_id)
    workflow.end_job = job_id
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

from flask import jsonify, render_template, request
from flask_login import login_required

from eNMS import db
from eNMS.base.custom_base import factory
from eNMS.base.helpers import retrieve
from eNMS.base.properties import pretty_names
from eNMS.objects.models import Device, Pool
from eNMS.scripts.models import Job
from eNMS.tasks.forms import CompareForm, SchedulingForm
from eNMS.tasks.models import Task
from eNMS.workflows import blueprint
from eNMS.workflows.forms import (
    AddExistingTaskForm,
    WorkflowEditorForm,
    WorkflowCreationForm
)
from eNMS.workflows.models import WorkflowEdge, Workflow


@blueprint.route('/workflow_management')
@login_required
def workflows():
    scheduling_form = SchedulingForm(request.form)
    scheduling_form.job.choices = Job.choices()
    return render_template(
        'workflow_management.html',
        names=pretty_names,
        scheduling_form=scheduling_form,
        fields=('name', 'description'),
        workflows=Workflow.serialize(),
        form=WorkflowCreationForm(request.form)
    )


@blueprint.route('/workflow_editor/')
@blueprint.route('/workflow_editor/<workflow_id>')
@login_required
def workflow_editor(workflow_id=None):
    add_existing_task_form = AddExistingTaskForm(request.form)
    workflow_editor_form = WorkflowEditorForm(request.form)
    workflow_editor_form.workflow.choices = Workflow.choices()
    workflow = retrieve(Workflow, id=workflow_id)
    scheduling_form = SchedulingForm(request.form)
    scheduling_form.job.choices = Job.choices()
    scheduling_form.devices.choices = Device.choices()
    scheduling_form.pools.choices = Pool.choices()
    add_existing_task_form.task.choices = Task.choices()
    return render_template(
        'workflow_editor.html',
        add_existing_task_form=add_existing_task_form,
        workflow_editor_form=workflow_editor_form,
        scheduling_form=scheduling_form,
        compare_form=CompareForm(request.form),
        names=pretty_names,
        workflow=workflow.serialized if workflow_id else None
    )


@blueprint.route('/get/<workflow_id>', methods=['POST'])
@login_required
def get_workflow(workflow_id):
    workflow = retrieve(Workflow, id=workflow_id)
    return jsonify(workflow.serialized if workflow else {})


@blueprint.route('/edit_workflow', methods=['POST'])
@login_required
def edit_workflow():
    return jsonify(factory(Workflow, **request.form.to_dict()).serialized)


@blueprint.route('/delete/<workflow_id>', methods=['POST'])
@login_required
def delete_workflow(workflow_id):
    workflow = retrieve(Workflow, id=workflow_id)
    db.session.delete(workflow)
    db.session.commit()
    return jsonify(workflow.name)


@blueprint.route('/add_node/<workflow_id>/<task_id>', methods=['POST'])
@login_required
def add_node(workflow_id, task_id):
    workflow = retrieve(Workflow, id=workflow_id)
    task = retrieve(Task, id=task_id)
    workflow.tasks.append(task)
    db.session.commit()
    return jsonify(task.serialized)


@blueprint.route('/delete_node/<workflow_id>/<task_id>', methods=['POST'])
@login_required
def delete_node(workflow_id, task_id):
    task = retrieve(Task, id=task_id)
    db.session.delete(task)
    db.session.commit()
    return jsonify(task.properties)


@blueprint.route('/add_edge/<wf_id>/<type>/<source>/<dest>', methods=['POST'])
@login_required
def add_edge(wf_id, type, source, dest):
    source_task = retrieve(Task, id=source)
    destination_task = retrieve(Task, id=dest)
    workflow_edge = factory(WorkflowEdge, **{
        'name': f'{source_task.name} -> {destination_task.name}',
        'workflow': retrieve(Workflow, id=wf_id),
        'type': type,
        'source': source_task,
        'destination': destination_task
    })
    return jsonify(workflow_edge.serialized)


@blueprint.route('/delete_edge/<workflow_id>/<edge_id>', methods=['POST'])
@login_required
def delete_edge(workflow_id, edge_id):
    edge = retrieve(WorkflowEdge, id=edge_id)
    db.session.delete(edge)
    db.session.commit()
    return jsonify(edge.properties)


@blueprint.route('/set_as_start/<workflow_id>/<task_id>', methods=['POST'])
@login_required
def set_as_start(workflow_id, task_id):
    workflow = retrieve(Workflow, id=workflow_id)
    workflow.start_task = task_id
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/set_as_end/<workflow_id>/<task_id>', methods=['POST'])
@login_required
def set_as_end(workflow_id, task_id):
    workflow = retrieve(Workflow, id=workflow_id)
    workflow.end_task = task_id
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/save_positions/<workflow_id>', methods=['POST'])
@login_required
def save_positions(workflow_id):
    workflow = retrieve(Workflow, id=workflow_id)
    for task_id, position in request.json.items():
        task = retrieve(Task, id=task_id)
        task.positions[workflow.name] = (position['x'], position['y'])
    db.session.commit()
    return jsonify({'success': True})

from flask import jsonify, render_template, request
from flask_login import login_required

from eNMS import db
from eNMS.base.custom_base import base_factory
from eNMS.base.helpers import get_obj
from eNMS.base.properties import pretty_names
from eNMS.objects.models import Node, Pool
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
    workflow = get_obj(Workflow, id=workflow_id)
    scheduling_form = SchedulingForm(request.form)
    scheduling_form.job.choices = Job.choices()
    scheduling_form.nodes.choices = Node.choices()
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
    workflow = get_obj(Workflow, id=workflow_id)
    return jsonify(workflow.serialized if workflow else {})


@blueprint.route('/edit_workflow', methods=['POST'])
@login_required
def edit_workflow():
    workflow = base_factory(Workflow, **request.form.to_dict())
    db.session.commit()
    return jsonify(workflow.serialized)


@blueprint.route('/delete/<workflow_id>', methods=['POST'])
@login_required
def delete_workflow(workflow_id):
    workflow = get_obj(Workflow, id=workflow_id)
    db.session.delete(workflow)
    db.session.commit()
    return jsonify(workflow.name)


@blueprint.route('/add_node/<workflow_id>/<task_id>', methods=['POST'])
@login_required
def add_node(workflow_id, task_id):
    workflow = get_obj(Workflow, id=workflow_id)
    task = get_obj(Task, id=task_id)
    workflow.tasks.append(task)
    db.session.commit()
    return jsonify(task.serialized)


@blueprint.route('/delete_node/<workflow_id>/<task_id>', methods=['POST'])
@login_required
def delete_node(workflow_id, task_id):
    task = get_obj(Task, id=task_id)
    db.session.delete(task)
    db.session.commit()
    return jsonify(task.properties)


@blueprint.route('/add_edge/<wf_id>/<type>/<source>/<dest>', methods=['POST'])
@login_required
def add_edge(wf_id, type, source, dest):
    source_task = get_obj(Task, id=source)
    destination_task = get_obj(Task, id=dest)
    workflow = get_obj(Workflow, id=wf_id)
    workflow_edge = WorkflowEdge(type, source_task, destination_task)
    db.session.add(workflow_edge)
    workflow.edges.append(workflow_edge)
    db.session.commit()
    return jsonify(workflow_edge.serialized)


@blueprint.route('/delete_edge/<workflow_id>/<edge_id>', methods=['POST'])
@login_required
def delete_edge(workflow_id, edge_id):
    edge = get_obj(WorkflowEdge, id=edge_id)
    db.session.delete(edge)
    db.session.commit()
    return jsonify(edge.properties)


@blueprint.route('/set_as_start/<workflow_id>/<task_id>', methods=['POST'])
@login_required
def set_as_start(workflow_id, task_id):
    workflow = get_obj(Workflow, id=workflow_id)
    workflow.start_task = task_id
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/save_positions', methods=['POST'])
@login_required
def save_positions():
    for task_id, position in request.json.items():
        task = get_obj(Task, id=task_id)
        task.x, task.y = position['x'], position['y']
    db.session.commit()
    return jsonify({'success': True})

from base.database import db, get_obj
from base.properties import pretty_names
from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required
from .forms import WorkflowEditorForm, WorkflowCreationForm
from .models import WorkflowEdge, Workflow, workflow_factory
from objects.models import Node, Pool
from scripts.models import Script
from tasks.forms import SchedulingForm
from tasks.models import Task

blueprint = Blueprint(
    'workflows_blueprint',
    __name__,
    url_prefix='/workflows',
    template_folder='templates',
    static_folder='static'
)

## Template rendering


@blueprint.route('/workflow_management')
@login_required
def workflows():
    return render_template(
        'workflow_management.html',
        names=pretty_names,
        fields=('name', 'description', 'type'),
        workflows=Workflow.serialize(),
        form=WorkflowCreationForm(request.form)
    )


@blueprint.route('/workflow_editor/')
@blueprint.route('/workflow_editor/<workflow_id>')
@login_required
def workflow_editor(workflow_id=None):
    workflow_editor_form = WorkflowEditorForm(request.form)
    workflow_editor_form.workflow.choices = Workflow.choices()
    workflow = get_obj(Workflow, id=workflow_id).serialized if workflow_id else None
    scheduling_form = SchedulingForm(request.form)
    scheduling_form.scripts.choices = Script.choices()
    scheduling_form.nodes.choices = Node.choices()
    scheduling_form.pools.choices = Pool.choices()
    return render_template(
        'workflow_editor.html',
        workflow_editor_form=workflow_editor_form,
        scheduling_form=scheduling_form,
        names=pretty_names,
        workflow=workflow
    )


## AJAX calls


@blueprint.route('/get/<workflow_id>', methods=['POST'])
@login_required
def get_workflow(workflow_id):
    workflow = get_obj(Workflow, id=workflow_id)
    return jsonify(workflow.serialized)


@blueprint.route('/edit_workflow', methods=['POST'])
@login_required
def edit_workflow():
    workflow = workflow_factory(**request.form.to_dict())
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
    return jsonify({})


@blueprint.route('/add_edge/<workflow_id>/<type>/<source>/<dest>', methods=['POST'])
@login_required
def add_edge(workflow_id, type, source_id, destination_id):
    source_task = get_obj(Task, id=source_id)
    destination_task = get_obj(Task, id=destination_id)
    workflow_edge = WorkflowEdge(type, source_task, destination_task)
    db.session.add(workflow_edge)
    workflow.edges.append(workflow_edge)
    db.session.commit()
    return jsonify({})


@blueprint.route('/set_as_start/<task_id>', methods=['POST'])
@login_required
def set_as_start(workflow_id, type, source_id, destination_id):
    get_obj(Workflow, id=workflow_id).start_script = get_obj(Task, id=start_id)
    db.session.commit()
    return jsonify({})

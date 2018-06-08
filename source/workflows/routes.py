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


@blueprint.route('/add_node/<workflow_id>/<script_id>', methods=['POST'])
@login_required
def add_node(workflow_id, script_id):
    workflow = get_obj(Workflow, id=workflow_id)
    script = get_obj(Script, id=script_id)
    return jsonify(script.serialized)


@blueprint.route('/save/<workflow_id>', methods=['POST'])
@login_required
def save_workflow(workflow_id):
    workflow = get_obj(Workflow, id=workflow_id)
    workflow.tasks = []
    for edge in workflow.edges:
        db.session.delete(edge)
    db.session.commit()
    for node in request.json['nodes']:
        task = get_obj(Task, id=node['id'])
        workflow.tasks.append(task)
    for edge in request.json['edges']:
        source = get_obj(Task, id=int(edge['from']))
        destination = get_obj(Task, id=int(edge['to']))
        workflow_edge = WorkflowEdge(edge['type'], source, destination)
        db.session.add(workflow_edge)
        db.session.commit()
        workflow.edges.append(workflow_edge)
    if request.json['start']:
        start_id = request.json['start']['id']
        workflow.start_script = get_obj(Task, id=start_id)
    db.session.commit()
    return jsonify({})

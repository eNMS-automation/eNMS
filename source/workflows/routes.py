from base.database import db, get_obj
from base.properties import pretty_names
from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required
from .forms import AddScriptForm, WorkflowCreationForm
from .models import ScriptEdge, Workflow, workflow_factory
from objects.models import Node, Pool
from scripts.forms import SchedulingForm
from scripts.models import default_scripts, Script
from scripts.routes import type_to_form

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
    scheduling_form = SchedulingForm(request.form)
    scheduling_form.nodes.choices = Node.choices()
    scheduling_form.pools.choices = Pool.choices()
    return render_template(
        'workflow_management.html',
        names=pretty_names,
        fields=('name', 'description', 'type'),
        workflows=Workflow.serialize(),
        form=WorkflowCreationForm(request.form),
        scheduling_form=scheduling_form
    )


@blueprint.route('/manage_<workflow>', methods=['GET', 'POST'])
@login_required
def workflow_editor(workflow):
    form = AddScriptForm(request.form)
    form.scripts.choices = [(s[0], s[0]) for s in default_scripts]
    workflow = get_obj(Workflow, name=workflow)
    return render_template(
        'workflow_editor.html',
        type_to_form={t: s(request.form) for t, s in type_to_form.items()},
        form=form,
        names=pretty_names,
        workflow=workflow
    )


## AJAX calls


@blueprint.route('/get_<workflow_id>', methods=['POST'])
@login_required
def get_workflow(workflow_id):
    workflow = get_obj(Workflow, id=workflow_id)
    properties = ('name', 'description', 'type')
    workflow_properties = {
        property: str(getattr(workflow, property))
        for property in properties
    }
    return jsonify(workflow_properties)


@blueprint.route('/edit_workflow', methods=['POST'])
@login_required
def edit_workflow():
    workflow = workflow_factory(**request.form.to_dict())
    db.session.commit()
    return jsonify({'name': workflow.name, 'id': workflow.id})


@blueprint.route('/delete_<workflow_id>', methods=['POST'])
@login_required
def delete_workflow(workflow_id):
    workflow = get_obj(Workflow, id=workflow_id)
    db.session.delete(workflow)
    db.session.commit()
    return jsonify(workflow.name)


@blueprint.route('/save_<workflow_id>', methods=['POST'])
@login_required
def save_workflow(workflow_id):
    id_to_script = {}
    workflow = get_obj(Workflow, id=workflow_id)
    workflow.scripts = []
    for edge in workflow.edges:
        db.session.delete(edge)
    db.session.commit()
    for node in request.json['nodes']:
        script = get_obj(Script, name=node['label'])
        id_to_script[node['id']] = node['label']
        workflow.scripts.append(script)
    for edge in request.json['edges']:
        source = get_obj(Script, name=id_to_script[edge['from']])
        destination = get_obj(Script, name=id_to_script[edge['to']])
        script_edge = ScriptEdge(edge['type'], source, destination)
        db.session.add(script_edge)
        db.session.commit()
        workflow.edges.append(script_edge)
    if request.json['start']:
        start_id = request.json['start']['id']
        workflow.start_script = get_obj(Script, id=start_id)
    db.session.commit()
    return jsonify({})

from base.database import db, get_obj
from base.properties import pretty_names
from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required
from .forms import AddScriptForm, WorkflowCreationForm
from .models import ScriptEdge, Workflow, workflow_factory
from scripts.models import Script

blueprint = Blueprint(
    'workflows_blueprint',
    __name__,
    url_prefix='/workflows',
    template_folder='templates',
    static_folder='static'
)


@blueprint.route('/overview', methods=['GET', 'POST'])
@login_required
def workflows():
    form = WorkflowCreationForm(request.form)
    return render_template(
        'workflow_management.html',
        names=pretty_names,
        fields=('name', 'description'),
        workflows=Workflow.query.all(),
        form=form
    )


@blueprint.route('/get_<name>', methods=['POST'])
@login_required
def get_workflow(name):
    workflow = get_obj(Workflow, name=name)
    properties = ('name', 'description', 'type')
    workflow_properties = {
        property: str(getattr(workflow, property))
        for property in properties
    }
    return jsonify(workflow_properties)


@blueprint.route('/edit_workflow', methods=['POST'])
@login_required
def edit_workflow():
    workflow_factory(**request.form.to_dict())
    db.session.commit()
    return jsonify({})


@blueprint.route('/delete_<name>', methods=['POST'])
@login_required
def delete_workflow(name):
    workflow = get_obj(Workflow, name=name)
    db.session.delete(workflow)
    db.session.commit()
    return jsonify({})


@blueprint.route('/manage_<workflow>', methods=['GET', 'POST'])
@login_required
def workflow_manager(workflow):
    form = AddScriptForm(request.form)
    form.scripts.choices = Script.choices()
    workflow = get_obj(Workflow, name=workflow)
    return render_template(
        'workflow_editor.html',
        form=form,
        workflow=workflow
    )


@blueprint.route('/save_<workflow>', methods=['POST'])
@login_required
def save_workflow(workflow):
    id_to_script = {}
    workflow = get_obj(Workflow, name=workflow)
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

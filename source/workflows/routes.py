from base.database import db
from base.properties import pretty_names
from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required
from .forms import AddScriptForm, WorkflowCreationForm
from .models import ScriptEdge, Workflow
from objects.models import get_obj
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
    return render_template(
        'workflow_overview.html',
        names=pretty_names,
        fields=('name', 'description'),
        workflows=Workflow.query.all(),
    )


@blueprint.route('/workflow_creation', methods=['GET', 'POST'])
@login_required
def workflow_creation():
    form = WorkflowCreationForm(request.form)
    if request.method == 'POST':
        workflow = Workflow(**request.form.to_dict())
        db.session.add(workflow)
        db.session.commit()
    return render_template(
        'workflow_creation.html',
        form=form
    )


@blueprint.route('/manage_<workflow>', methods=['GET', 'POST'])
@login_required
def workflow_manager(workflow):
    form = AddScriptForm(request.form)
    form.scripts.choices = Script.choices()
    workflow = get_obj(db, Workflow, name=workflow)
    return render_template(
        'workflow_manager.html',
        form=form,
        workflow=workflow
    )


@blueprint.route('/save_<workflow>', methods=['POST'])
@login_required
def save_workflow(workflow):
    id_to_script = {}
    workflow = get_obj(db, Workflow, name=workflow)
    for edge in workflow.edges:
        db.session.delete(edge)
    db.session.commit()
    for node in request.json['nodes']:
        script = get_obj(db, Script, name=node['label'])
        id_to_script[node['id']] = node['label']
        workflow.scripts.append(script)
    for edge in request.json['edges']:
        source = get_obj(db, Script, name=id_to_script[edge['from']])
        destination = get_obj(db, Script, name=id_to_script[edge['to']])
        script_edge = ScriptEdge(source, destination)
        db.session.add(script_edge)
        db.session.commit()
        workflow.edges.append(script_edge)
    if request.json['start']:
        start_id = request.json['start']['id']
        workflow.start_script = get_obj(db, Script, id=start_id)
    db.session.commit()
    return jsonify({})

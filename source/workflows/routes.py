from base.database import db
from base.properties import pretty_names
from flask import Blueprint, render_template, request
from flask_login import login_required
from .forms import AddScriptForm, WorkflowCreationForm
from .models import Workflow
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
    return render_template(
        'workflow_manager.html',
        form=form
    )
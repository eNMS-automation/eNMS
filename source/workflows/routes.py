from flask import Blueprint, render_template, request
from flask_login import login_required
from .forms import AddScriptForm
from scripts.models import Script

blueprint = Blueprint(
    'workflows_blueprint',
    __name__,
    url_prefix='/workflow',
    template_folder='templates',
    static_folder='static'
)


@blueprint.route('/workflow_creation', methods=['GET', 'POST'])
@login_required
def workflow_creation():
    form = AddScriptForm(request.form)
    form.scripts.choices = Script.choices()
    return render_template(
        'workflow.html',
        form=form
    )

from flask import Blueprint, render_template, request
from flask_login import login_required
from .models import Workflow
from scripts.models import Script

blueprint = Blueprint(
    'workflow_blueprint',
    __name__,
    url_prefix='/workflow',
    template_folder='templates',
    static_folder='static'
)


@blueprint.route('/<script_type>_configuration', methods=['GET', 'POST'])
@login_required
def configuration(script_type):
    form = {
        'netmiko': NetmikoConfigScriptForm,
        'napalm': NapalmConfigScriptForm
        }[script_type](request.form)
    if 'create_script' in request.form:
        # retrieve the raw script: we will use it as-is or update it depending
        # on the type of script (jinja2-enabled template or not)
        content = request.form['text']
        if form.data['content_type'] != 'simple':
            file = request.files['file']
            filename = secure_filename(file.filename)
            if allowed_file(filename, {'yaml', 'yml'}):
                parameters = load(file.read())
                template = Template(content)
                content = template.render(**parameters)
        script = {
            'netmiko': NetmikoConfigScript,
            'napalm': NapalmConfigScript
            }[script_type](content, **request.form)
        db.session.add(script)
        db.session.commit()
    return render_template(
        script_type + '_configuration.html',
        form=form
    )


@blueprint.route('/workflow_creation', methods=['GET', 'POST'])
@login_required
def workflow_creation():
    # form = 
    return render_template(
        'workflow.html',
    )
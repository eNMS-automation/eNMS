from base.database import db
from base.helpers import allowed_file
from flask import Blueprint, current_app, render_template, request
from flask_login import login_required
from .forms import *
from jinja2 import Template
from yaml import load
from .models import *
from os.path import join
from werkzeug import secure_filename

blueprint = Blueprint(
    'scripts_blueprint', 
    __name__, 
    url_prefix = '/scripts',
    template_folder = 'templates',
    static_folder = 'static'
    )

@blueprint.route('/script_creation', methods=['GET', 'POST'])
@login_required
def script_creation():
    form = ScriptCreationForm(request.form)
    if 'create_script' in request.form:
        # retrieve the raw script: we will use it as-is or update it depending
        # on the type of script (jinja2-enabled template or not)
        content = request.form['text']
        if form.data['type'] != 'simple':
            try:
                file = request.files['file']
                if allowed_file(file.filename, {'yaml'}):
                    filename = secure_filename(file.filename)
                    parameters = load(file.read())
                    template = Template(content)
                    content = template.render(**parameters)
                else:
                    raise Exception
            except Exception as e:
                #TODO beautiful warning with the exception
                print(e)
        script = ClassicScript(content, **request.form)
        db.session.add(script)
        db.session.commit()
    return render_template(
        'script_creation.html',
        form = form
        )

@blueprint.route('/ansible_script', methods=['GET', 'POST'])
@login_required
def ansible_script():
    form = AnsibleScriptForm(request.form)
    if request.method == 'POST':
        script = AnsibleScript(**request.form)
        db.session.add(script)
        db.session.commit()
    return render_template(
        'ansible_script.html',
        form = form
        )
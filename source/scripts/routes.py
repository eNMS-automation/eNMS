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
            filename = request.files['file'].filename
            if 'file' in request.files and filename:
                if allowed_file(filename, {'yaml'}):
                    filename = secure_filename(filename)
                    filepath = join(current_app.config['UPLOAD_FOLDER'], filename)
                    with open(filepath, 'r') as f:
                        parameters = load(f)
                    template = Template(content)
                    content = template.render(**parameters)
                    print(content)
                #TODO properly display that error in the GUI
                else:
                    flash('file {}: format not allowed'.format(filename))
        script = Script(content, **request.form)
        db.session.add(script)
        db.session.commit()
    return render_template(
        'script_creation.html',
        form = form
        )

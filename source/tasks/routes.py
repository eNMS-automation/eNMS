from base.database import db
from base.helpers import str_dict
from difflib import ndiff, unified_diff
from flask import Blueprint, render_template, request
from flask_login import login_required
from .forms import *
from .models import Task
from objects.models import get_obj

blueprint = Blueprint(
    'tasks_blueprint', 
    __name__, 
    url_prefix = '/tasks', 
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

@blueprint.route('/task_management', methods=['GET', 'POST'])
@login_required
def task_management():
    if 'compare' in request.form:
        n1, n2 = request.form['first_node'], request.form['second_node']
        t1, t2 = request.form['first_version'], request.form['second_version']
        task = get_obj(db, Task, name=request.form['task_name'])
        # get the two versions of the logs
        v1 = str_dict(task.logs[t1][n1]).splitlines()
        v2 = str_dict(task.logs[t2][n2]).splitlines()
        print(v1, v2)
        return render_template(
            'compare.html',
            ndiff = '\n'.join(ndiff(v1, v2)),
            unified_diff = '\n'.join(unified_diff(v1, v2)),
            )
    tasks = Task.query.all()
    form_per_task = {}
    for task in filter(lambda t: t.recurrent, tasks):
        form = CompareForm(request.form)
        form.first_node.choices = [(i, i) for (i, _, _, _) in task.nodes]
        form.second_node.choices = form.first_node.choices
        versions = [(v, v) for v in tuple(task.logs)]
        form.first_version.choices = form.second_version.choices = versions
        form_per_task[task.name] = form
    # task.logs is a dictionnary and we need to keep that way, but for properly
    # outputtng it's content, we will use str_dict
    log_per_task = {task.name: str_dict(task.logs) for task in tasks}
    return render_template(
        'task_management.html',
        tasks = tasks,
        log_per_task = log_per_task,
        form_per_task = form_per_task
        )
        
@blueprint.route('/delete_task', methods=['POST'])
@login_required
def delete_task():
    #TODO remove the job from the scheduler...
    task = Task.query.filter_by(name=request.form['task_name']).first()
    print(task)
    Task.query.filter_by(name=request.form['task_name']).delete()
    db.session.commit()
    return task_management()
    
@blueprint.route('/pause_task', methods=['POST'])
@login_required
def pause_task():
    task = Task.query.filter_by(name=request.form['task_name']).first()
    task.pause_task()
    return task_management()
    
@blueprint.route('/resume_task', methods=['POST'])
@login_required
def resume_task():
    task = Task.query.filter_by(name=request.form['task_name']).first()
    task.resume_task()
    return task_management()
    
@blueprint.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')

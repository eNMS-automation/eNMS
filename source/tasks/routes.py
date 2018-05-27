from base.database import db, get_obj
from base.helpers import str_dict
from difflib import SequenceMatcher
from flask import Blueprint, jsonify, render_template, request, session
from flask_login import current_user, login_required
from .forms import CompareForm
from .models import Task, task_factory
from objects.models import Filter, Node
from scripts.models import Script
from re import search, sub
from views.forms import SchedulingForm
from workflows.models import Workflow

blueprint = Blueprint(
    'tasks_blueprint',
    __name__,
    url_prefix='/tasks',
    template_folder='templates',
    static_folder='static'
)

## Template rendering


@blueprint.route('/task_management')
@login_required
def task_management():
    scheduling_form = SchedulingForm(request.form)
    scheduling_form.scripts.choices = Script.choices()
    scheduling_form.workflows.choices = Workflow.choices()
    tasks = Task.query.all()
    return render_template(
        'task_management.html',
        tasks=tasks,
        compare_form=CompareForm(request.form),
        scheduling_form=scheduling_form
    )


@blueprint.route('/calendar')
@login_required
def calendar():
    scheduling_form = SchedulingForm(request.form)
    scheduling_form.scripts.choices = Script.choices()
    scheduling_form.workflows.choices = Workflow.choices()
    tasks = {}
    for task in Task.query.all():
        # javascript dates range from 0 to 11, we must account for that by
        # substracting 1 to the month for the date to be properly displayed in
        # the calendar
        python_month = search(r'.*-(\d{2})-.*', task.start_date).group(1)
        month = '{:02}'.format((int(python_month) - 1) % 12)
        tasks[task] = sub(
            r"(\d+)-(\d+)-(\d+) (\d+):(\d+).*",
            r"\1, " + month + r", \3, \4, \5",
            task.start_date
        )
    return render_template(
        'calendar.html',
        tasks=tasks,
        scheduling_form=scheduling_form
    )


## AJAX calls


@blueprint.route('/view_scheduler', methods=['POST'])
@login_required
def view_scheduler():
    data = request.form.to_dict()
    selection = map(int, session['selection'])
    scripts = request.form.getlist('scripts')
    workflows = request.form.getlist('workflows')
    data['scripts'] = [get_obj(Script, name=name) for name in scripts]
    data['workflows'] = [get_obj(Workflow, name=name) for name in workflows]
    data['nodes'] = [get_obj(Node, id=id) for id in selection]
    data['user'] = current_user
    task_factory(**data)
    return jsonify({})


@blueprint.route('/job_scheduler/<type>/<name>', methods=['POST'])
@login_required
def job_scheduler(type, name):
    cls = Script if type == 'script' else Workflow
    data = request.form.to_dict()
    data['scripts'] = [get_obj(cls, name=name)] if type == 'script' else []
    data['workflows'] = [get_obj(cls, name=name)] if type == 'workflow' else []
    data['nodes'] = [get_obj(Node, name=n) for n in request.form.getlist('nodes')]
    for filter in request.form.getlist('filters'):
        data['nodes'].extend(get_obj(Filter, name=filter).nodes)
    data['user'] = current_user
    task_factory(**data)
    return jsonify({})


@blueprint.route('/get/<name>', methods=['POST'])
@login_required
def get_task(name):
    task = get_obj(Task, name=name)
    task_properties = {
        property: str(getattr(task, property))
        for property in Task.properties
    }
    # prepare the data for javascript
    for p in ('scripts', 'workflows'):
        task_properties[p] = task_properties[p].replace(', ', ',')[1:-1].split(',')
    return jsonify(task_properties)


@blueprint.route('/show_logs/<name>', methods=['POST'])
@login_required
def show_logs(name):
    task = get_obj(Task, name=name)
    return jsonify(str_dict(task.logs))


@blueprint.route('/get_diff/<name>/<v1>/<v2>/<n1>/<n2>/<s1>/<s2>', methods=['POST'])
@login_required
def get_diff(name, v1, v2, n1, n2, s1, s2):
    task = get_obj(Task, name=name)
    first = str_dict(task.logs[v1][s1][n1]).splitlines()
    second = str_dict(task.logs[v2][s2][n2]).splitlines()
    opcodes = SequenceMatcher(None, first, second).get_opcodes()
    return jsonify({
        'first': first,
        'second': second,
        'opcodes': opcodes,
    })


@blueprint.route('/compare_logs/<name>', methods=['POST'])
@login_required
def compare_logs(name):
    task = get_obj(Task, name=name)
    results = {
        'nodes': [node.name for node in task.nodes],
        'scripts': [script.name for script in task.scripts],
        'versions': list(task.logs)
    }
    return jsonify(results)


@blueprint.route('/delete_task/<name>', methods=['POST'])
@login_required
def delete_task(name):
    task = Task.query.filter_by(name=name).first()
    task.delete_task()
    db.session.delete(task)
    db.session.commit()
    return task_management()


@blueprint.route('/pause_task/<name>', methods=['POST'])
@login_required
def pause_task(name):
    task = Task.query.filter_by(name=name).first()
    task.pause_task()
    return task_management()


@blueprint.route('/resume_task/<name>', methods=['POST'])
@login_required
def resume_task(name):
    task = Task.query.filter_by(name=name).first()
    task.resume_task()
    return task_management()

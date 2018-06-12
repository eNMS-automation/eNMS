from difflib import SequenceMatcher
from flask import jsonify, render_template, request
from flask_login import current_user, login_required
from re import search, sub


from eNMS import db
from eNMS.base.helpers import get_obj, str_dict
from eNMS.base.properties import task_public_properties
from eNMS.tasks import blueprint
from eNMS.tasks.forms import CompareForm, SchedulingForm
from eNMS.tasks.models import ScheduledTask, Task, task_factory
from eNMS.objects.models import Pool, Node
from eNMS.scripts.models import Script
from eNMS.workflows.models import Workflow


## Template rendering


@blueprint.route('/task_management')
@login_required
def task_management():
    scheduling_form = SchedulingForm(request.form)
    scheduling_form.scripts.choices = Script.choices()
    return render_template(
        'task_management.html',
        fields=task_public_properties,
        tasks=ScheduledTask.serialize(),
        compare_form=CompareForm(request.form),
        scheduling_form=scheduling_form
    )


@blueprint.route('/calendar')
@login_required
def calendar():
    scheduling_form = SchedulingForm(request.form)
    scheduling_form.scripts.choices = Script.choices()
    tasks = {}
    for task in ScheduledTask.query.all():
        # javascript dates range from 0 to 11, we must account for that by
        # substracting 1 to the month for the date to be properly displayed in
        # the calendar
        python_month = search(r'.*-(\d{2})-.*', task.start_date).group(1)
        month = '{:02}'.format((int(python_month) - 1) % 12)
        js_date = [int(i) for i in sub(
            r"(\d+)-(\d+)-(\d+) (\d+):(\d+).*",
            r"\1," + month + r",\3,\4,\5",
            task.start_date
        ).split(',')]
        tasks[task.name] = {
            'date': js_date,
        }
    return render_template(
        'calendar.html',
        tasks=tasks,
        scheduling_form=scheduling_form
    )


## AJAX calls


@blueprint.route('/scheduler/<task_type>', methods=['POST'])
@blueprint.route('/scheduler/<task_type>/<workflow_id>', methods=['POST'])
@login_required
def scheduler(task_type, workflow_id=None):
    data = request.form.to_dict()
    if task_type in ('script_task', 'inner_task'):
        scripts = request.form.getlist('scripts')
        nodes = request.form.getlist('nodes')
        data['scripts'] = [get_obj(Script, id=id) for id in scripts]
        data['nodes'] = [get_obj(Node, id=id) for id in nodes]
        print(request.form.getlist('pools'))
        for pool_id in request.form.getlist('pools'):
            data['nodes'].extend(get_obj(Pool, id=pool_id).nodes)
    if task_type in ('workflow_task', 'inner_task'):
        data['workflow'] = get_obj(Workflow, id=workflow_id)
    data['user'] = current_user
    print(task_type, data)
    task = task_factory(task_type, **data)
    return jsonify(task.serialized)


@blueprint.route('/get/<task_id>', methods=['POST'])
@login_required
def get_task(task_id):
    task = get_obj(Task, id=task_id)
    return jsonify(task.serialized)


@blueprint.route('/show_logs/<task_id>', methods=['POST'])
@login_required
def show_logs(task_id):
    task = get_obj(Task, id=task_id)
    return jsonify(str_dict(task.logs))


@blueprint.route('/get_diff/<task_id>/<v1>/<v2>/<n1>/<n2>/<s1>/<s2>', methods=['POST'])
@login_required
def get_diff(task_id, v1, v2, n1, n2, s1, s2):
    task = get_obj(Task, id=task_id)
    first = str_dict(task.logs[v1][s1][n1]).splitlines()
    second = str_dict(task.logs[v2][s2][n2]).splitlines()
    opcodes = SequenceMatcher(None, first, second).get_opcodes()
    return jsonify({
        'first': first,
        'second': second,
        'opcodes': opcodes,
    })


@blueprint.route('/compare_logs/<task_id>', methods=['POST'])
@login_required
def compare_logs(task_id):
    task = get_obj(Task, id=task_id)
    results = {
        'nodes': [node.name for node in task.nodes],
        'scripts': [script.name for script in task.scripts],
        'versions': list(task.logs)
    }
    return jsonify(results)


@blueprint.route('/delete_task/<task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.filter_by(id=task_id).first()
    task.delete_task()
    db.session.delete(task)
    db.session.commit()
    return jsonify(task.name)


@blueprint.route('/pause_task/<task_id>', methods=['POST'])
@login_required
def pause_task(task_id):
    task = Task.query.filter_by(id=task_id).first()
    task.pause_task()
    return task_management()


@blueprint.route('/resume_task/<task_id>', methods=['POST'])
@login_required
def resume_task(task_id):
    task = Task.query.filter_by(id=task_id).first()
    task.resume_task()
    return task_management()

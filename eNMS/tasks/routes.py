from difflib import SequenceMatcher
from flask import jsonify, render_template, request
from flask_login import current_user, login_required
from re import search, sub

from eNMS import db
from eNMS.base.helpers import get_obj, str_dict
from eNMS.base.properties import task_public_properties
from eNMS.tasks import blueprint
from eNMS.tasks.forms import CompareForm, SchedulingForm
from eNMS.tasks.models import Task, task_factory
from eNMS.objects.models import Pool, Node
from eNMS.scripts.models import Job
from eNMS.workflows.models import Workflow


## Template rendering


@blueprint.route('/task_management')
@login_required
def task_management():
    scheduling_form = SchedulingForm(request.form)
    scheduling_form.nodes.choices = Node.choices()
    scheduling_form.pools.choices = Pool.choices()
    scheduling_form.job.choices = Job.choices()
    return render_template(
        'task_management.html',
        fields=task_public_properties,
        tasks=Task.serialize(),
        compare_form=CompareForm(request.form),
        scheduling_form=scheduling_form
    )


@blueprint.route('/calendar')
@login_required
def calendar():
    scheduling_form = SchedulingForm(request.form)
    scheduling_form.job.choices = Job.choices()
    tasks = {}
    for task in Task.query.all():
        # javascript dates range from 0 to 11, we must account for that by
        # substracting 1 to the month for the date to be properly displayed in
        # the calendar
        if not task.start_date:
            continue
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


@blueprint.route('/scheduler', methods=['POST'])
@blueprint.route('/scheduler/<workflow_id>', methods=['POST'])
@login_required
def scheduler(workflow_id=None):
    print(request.form)
    data = request.form.to_dict()
    data['job'] = get_obj(Job, id=data['job'])
    data['nodes'] = [get_obj(Node, id=id) for id in request.form.getlist('nodes')]
    data['pools'] = [get_obj(Pool, id=id) for id in request.form.getlist('pools')]
    data['workflow'] = get_obj(Workflow, id=workflow_id)
    data['user'] = current_user
    task = task_factory(**data)
    return jsonify(task.serialized)


@blueprint.route('/add_to_workflow/<workflow_id>', methods=['POST'])
@login_required
def add_to_workflow(workflow_id):
    print(request.form)
    workflow = get_obj(Workflow, id=workflow_id)
    task = get_obj(Task, id=request.form['task'])
    task.workflows.append(workflow)
    db.session.commit()
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


@blueprint.route('/get_diff/<task_id>/<v1>/<v2>/<n1>/<n2>', methods=['POST'])
@login_required
def get_diff(task_id, v1, v2, n1, n2):
    task = get_obj(Task, id=task_id)
    first = str_dict(task.logs[v1][n1]).splitlines()
    second = str_dict(task.logs[v2][n2]).splitlines()
    opcodes = SequenceMatcher(None, first, second).get_opcodes()
    return jsonify({'first': first, 'second': second, 'opcodes': opcodes})


@blueprint.route('/compare_logs/<task_id>', methods=['POST'])
@login_required
def compare_logs(task_id):
    task = get_obj(Task, id=task_id)
    results = {
        'nodes': [node.name for node in task.nodes],
        'versions': list(task.logs)
    }
    return jsonify(results)


@blueprint.route('/run_task/<task_id>', methods=['POST'])
@login_required
def run_task(task_id):
    task = Task.query.filter_by(id=task_id).first()
    task.schedule(run_now=True)
    return jsonify(task.serialized)


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

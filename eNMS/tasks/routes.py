from difflib import SequenceMatcher
from flask import jsonify, render_template, request
from flask_login import current_user, login_required
from re import search, sub

from eNMS import db
from eNMS.base.custom_base import factory
from eNMS.base.helpers import retrieve, str_dict
from eNMS.base.properties import task_public_properties
from eNMS.tasks import blueprint
from eNMS.tasks.forms import CompareForm, SchedulingForm
from eNMS.tasks.models import ScriptTask, Task, WorkflowTask
from eNMS.objects.models import Pool, Device
from eNMS.scripts.models import Job
from eNMS.workflows.models import Workflow


@blueprint.route('/task_management')
@login_required
def task_management():
    scheduling_form = SchedulingForm(request.form)
    scheduling_form.devices.choices = Device.choices()
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
        python_month = search(
            r'.*-(\d{2})-.*',
            task.aps_date('start_date')
        ).group(1)
        month = '{:02}'.format((int(python_month) - 1) % 12)
        js_date = [int(i) for i in sub(
            r"(\d+)-(\d+)-(\d+) (\d+):(\d+).*",
            r"\1," + month + r",\3,\4,\5",
            task.aps_date('start_date')
        ).split(',')]
        tasks[task.name] = {
            'date': js_date,
        }
    return render_template(
        'calendar.html',
        tasks=tasks,
        scheduling_form=scheduling_form
    )


@blueprint.route('/scheduler', methods=['POST'])
@login_required
def scheduler(workflow_id=None):
    data = request.form.to_dict()
    data['job'] = retrieve(Job, id=data['job'])
    data['devices'] = [
        retrieve(Device, id=id) for id in request.form.getlist('devices')
    ]
    data['pools'] = [
        retrieve(Pool, id=id) for id in request.form.getlist('pools')
    ]
    data['user'] = current_user
    cls = WorkflowTask if data['job'].type == 'workflow' else ScriptTask
    task = factory(cls, **data)
    return jsonify(task.serialized)


@blueprint.route('/add_to_workflow/<workflow_id>', methods=['POST'])
@login_required
def add_to_workflow(workflow_id):
    workflow = retrieve(Workflow, id=workflow_id)
    task = retrieve(Task, id=request.form['task'])
    task.workflows.append(workflow)
    db.session.commit()
    return jsonify(task.serialized)


@blueprint.route('/get/<task_id>', methods=['POST'])
@login_required
def get_task(task_id):
    return jsonify(retrieve(Task, id=task_id).serialized)


@blueprint.route('/show_logs/<task_id>', methods=['POST'])
@login_required
def show_logs(task_id):
    return jsonify(str_dict(retrieve(Task, id=task_id).logs))


@blueprint.route('/get_diff/<task_id>/<v1>/<v2>/<n1>/<n2>', methods=['POST'])
@login_required
def get_diff(task_id, v1, v2, n1, n2):
    task = retrieve(Task, id=task_id)
    first = str_dict(task.logs[v1]['logs'][n1]).splitlines()
    second = str_dict(task.logs[v2]['logs'][n2]).splitlines()
    opcodes = SequenceMatcher(None, first, second).get_opcodes()
    return jsonify({'first': first, 'second': second, 'opcodes': opcodes})


@blueprint.route('/compare_logs/<task_id>', methods=['POST'])
@login_required
def compare_logs(task_id):
    task = retrieve(Task, id=task_id)
    results = {
        'devices': [device.name for device in task.devices],
        'versions': list(task.logs)
    }
    return jsonify(results)


@blueprint.route('/run_task/<task_id>', methods=['POST'])
@login_required
def run_task(task_id):
    task = retrieve(Task, id=task_id)
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

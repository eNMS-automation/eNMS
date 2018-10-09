from difflib import SequenceMatcher
from flask import jsonify, render_template, request
from flask_login import current_user, login_required
from json import dumps
from re import search, sub

from eNMS import db
from eNMS.base.custom_base import factory
from eNMS.base.helpers import permission_required, retrieve, str_dict
from eNMS.base.properties import task_public_properties
from eNMS.tasks import blueprint
from eNMS.tasks.forms import CompareLogsForm, SchedulingForm
from eNMS.tasks.models import ServiceTask, Task, WorkflowTask
from eNMS.objects.models import Pool, Device
from eNMS.services.models import Job
from eNMS.workflows.models import Workflow


@blueprint.route('/task_management/<task_type>')
@login_required
@permission_required('Tasks section')
def task_management(task_type):
    scheduling_form = SchedulingForm(request.form)
    scheduling_form.devices.choices = Device.choices()
    scheduling_form.pools.choices = Pool.choices()
    scheduling_form.job.choices = Job.choices()
    task_class = ServiceTask if task_type == 'service' else WorkflowTask
    return render_template(
        f'{task_type}_tasks.html',
        compare_logs_form=CompareLogsForm(request.form),
        fields=task_public_properties,
        tasks=task_class.serialize(),
        scheduling_form=scheduling_form
    )


@blueprint.route('/calendar')
@login_required
@permission_required('Tasks section')
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
@permission_required('Schedule tasks', redirect=False)
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
    cls = WorkflowTask if data['job'].type == 'workflow' else ServiceTask
    task = factory(cls, **data)
    return jsonify(task.serialized)


@blueprint.route('/add_to_workflow/<workflow_id>', methods=['POST'])
@login_required
@permission_required('Edit tasks', redirect=False)
def add_to_workflow(workflow_id):
    workflow = retrieve(Workflow, id=workflow_id)
    task = retrieve(Task, id=request.form['task'])
    task.workflows.append(workflow)
    db.session.commit()
    return jsonify(task.serialized)


@blueprint.route('/get/<task_id>', methods=['POST'])
@login_required
@permission_required('Tasks section', redirect=False)
def get_task(task_id):
    return jsonify(retrieve(Task, id=task_id).serialized)


@blueprint.route('/run_task/<task_id>', methods=['POST'])
@login_required
@permission_required('Schedule tasks', redirect=False)
def run_task(task_id):
    task = retrieve(Task, id=task_id)
    task.schedule(run_now=True)
    return jsonify(task.serialized)


@blueprint.route('/delete_task/<task_id>', methods=['POST'])
@login_required
@permission_required('Edit tasks', redirect=False)
def delete_task(task_id):
    task = Task.query.filter_by(id=task_id).first()
    task.delete_task()
    db.session.delete(task)
    db.session.commit()
    return jsonify(task.name)


@blueprint.route('/pause_task/<task_id>', methods=['POST'])
@login_required
@permission_required('Schedule tasks', redirect=False)
def pause_task(task_id):
    task = Task.query.filter_by(id=task_id).first()
    task.pause_task()
    return jsonify({})


@blueprint.route('/resume_task/<task_id>', methods=['POST'])
@login_required
@permission_required('Schedule tasks', redirect=False)
def resume_task(task_id):
    task = Task.query.filter_by(id=task_id).first()
    task.resume_task()
    return jsonify({})

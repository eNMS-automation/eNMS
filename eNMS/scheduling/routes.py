from flask import jsonify, render_template, request
from flask_login import current_user, login_required
from re import search, sub

from eNMS import db
from eNMS.base.custom_base import factory
from eNMS.base.helpers import permission_required, fetch
from eNMS.base.properties import task_public_properties
from eNMS.scheduling import blueprint
from eNMS.scheduling.forms import SchedulingForm
from eNMS.scheduling.models import Task
from eNMS.automation.models import Job


@blueprint.route('/task_management')
@login_required
@permission_required('Scheduling Section')
def task_management():
    scheduling_form = SchedulingForm(request.form)
    scheduling_form.job.choices = Job.choices()
    return render_template(
        f'task_management.html',
        fields=task_public_properties,
        tasks=Task.serialize(),
        scheduling_form=scheduling_form
    )


@blueprint.route('/calendar')
@login_required
@permission_required('Scheduling Section')
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
        tasks[task.name] = {**task.serialized, **{'date': js_date}}
    return render_template(
        'calendar.html',
        tasks=tasks,
        scheduling_form=scheduling_form
    )


@blueprint.route('/scheduler', methods=['POST'])
@login_required
@permission_required('Edit Scheduling Section', redirect=False)
def scheduler(workflow_id=None):
    data = request.form.to_dict()
    data['job'] = fetch(Job, id=data['job'])
    data['user'] = current_user
    task = factory(Task, **data)
    return jsonify(task.serialized)


@blueprint.route('/get/<task_id>', methods=['POST'])
@login_required
@permission_required('Scheduling Section', redirect=False)
def get_task(task_id):
    return jsonify(fetch(Task, id=task_id).serialized)


@blueprint.route('/delete_task/<task_id>', methods=['POST'])
@login_required
@permission_required('Edit Scheduling Section', redirect=False)
def delete_task(task_id):
    task = Task.query.filter_by(id=task_id).first()
    task.delete_task()
    db.session.delete(task)
    db.session.commit()
    return jsonify(task.name)


@blueprint.route('/pause_task/<task_id>', methods=['POST'])
@login_required
@permission_required('Edit Scheduling Section', redirect=False)
def pause_task(task_id):
    task = Task.query.filter_by(id=task_id).first()
    task.pause_task()
    return jsonify({})


@blueprint.route('/resume_task/<task_id>', methods=['POST'])
@login_required
@permission_required('Edit Scheduling Section', redirect=False)
def resume_task(task_id):
    task = Task.query.filter_by(id=task_id).first()
    task.resume_task()
    return jsonify({})

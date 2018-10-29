from flask import jsonify, render_template, request
from flask_login import current_user
from re import search, sub

from eNMS import db
from eNMS.base.helpers import factory, fetch, get, post
from eNMS.base.properties import task_public_properties
from eNMS.scheduling import bp
from eNMS.scheduling.forms import SchedulingForm


@get(bp, '/task_management', 'Scheduling Section')
def task_management():
    scheduling_form = SchedulingForm(request.form)
    scheduling_form.job.choices = Job.choices()
    return render_template(
        f'task_management.html',
        fields=task_public_properties,
        tasks=Task.serialize(),
        scheduling_form=scheduling_form
    )


@get(bp, '/calendar', 'Scheduling Section')
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


@post(bp, '/scheduler', 'Edit Scheduling Section')
def scheduler(workflow_id=None):
    data = request.form.to_dict()
    data['job'] = fetch('Job', id=data['job'])
    data['user'] = current_user
    task = factory(Task, **data)
    return jsonify(task.serialized)


@post(bp, '/get/<task_id>', 'Scheduling Section')
def get_task(task_id):
    return jsonify(fetch('Task', id=task_id).serialized)


@post(bp, '/delete_task/<task_id>', 'Edit Scheduling Section')
def delete_task(task_id):
    task = Task.query.filter_by(id=task_id).first()
    task.delete_task()
    db.session.delete(task)
    db.session.commit()
    return jsonify(task.name)


@post(bp, '/pause_task/<task_id>', 'Edit Scheduling Section')
def pause_task(task_id):
    task = Task.query.filter_by(id=task_id).first()
    task.pause_task()
    return jsonify(True)


@post(bp, '/resume_task/<task_id>', 'Edit Scheduling Section')
def resume_task(task_id):
    task = Task.query.filter_by(id=task_id).first()
    task.resume_task()
    return jsonify(True)

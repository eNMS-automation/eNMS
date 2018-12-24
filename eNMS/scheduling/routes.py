from apscheduler.jobstores.base import JobLookupError
from flask import request
from re import search, sub

from eNMS.main import scheduler
from eNMS.base.helpers import (
    fetch,
    fetch_all,
    get,
    post,
    serialize
)
from eNMS.base.properties import task_public_properties
from eNMS.scheduling import bp
from eNMS.scheduling.forms import SchedulingForm


@get(bp, '/task_management', 'View')
def task_management():
    return dict(
        fields=task_public_properties,
        tasks=serialize('Task'),
        scheduling_form=SchedulingForm(request.form)
    )


@get(bp, '/calendar', 'View')
def calendar():
    tasks = {}
    for task in fetch_all('Task'):
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
    return dict(
        tasks=tasks,
        scheduling_form=SchedulingForm(request.form)
    )


@post(bp, '/scheduler/<action>', 'Admin')
def scheduler_action(action):
    getattr(scheduler, action)()
    return True


@post(bp, '/<action>_task/<task_id>', 'Edit')
def task_action(action, task_id):
    task = fetch('Task', id=task_id)
    try:
        getattr(task, action)()
    except JobLookupError:
        task.reschedule()
        getattr(task, action)()
    return True


@post(bp, '/get_status', 'View')
def get_status():
    return [task.status for task in fetch_all('Task')]

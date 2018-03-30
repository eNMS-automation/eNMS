from base.database import db
from base.helpers import str_dict
from difflib import ndiff, unified_diff
from flask import Blueprint, render_template, request
from flask_login import login_required
from .forms import CompareForm
from .models import Task
from objects.models import get_obj
from re import search, sub

blueprint = Blueprint(
    'tasks_blueprint',
    __name__,
    url_prefix='/tasks',
    template_folder='templates',
    static_folder='static'
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
        return render_template(
            'compare.html',
            ndiff='\n'.join(ndiff(v1, v2)),
            unified_diff='\n'.join(unified_diff(v1, v2)),
        )
    tasks = Task.query.all()
    form_per_task = {}
    for task in filter(lambda t: t.recurrent, tasks):
        form = CompareForm(request.form)
        form.first_node.choices = [(i, i) for i in task.nodes]
        form.second_node.choices = form.first_node.choices
        versions = [(v, v) for v in tuple(task.logs)]
        form.first_version.choices = form.second_version.choices = versions
        form_per_task[task.name] = form
    # task.logs is a dictionnary and we need to keep that way, but for properly
    # outputtng it's content, we will use str_dict
    log_per_task = {task.name: str_dict(task.logs) for task in tasks}
    return render_template(
        'task_management.html',
        tasks=tasks,
        log_per_task=log_per_task,
        form_per_task=form_per_task
    )


@blueprint.route('/delete_task', methods=['POST'])
@login_required
def delete_task():
    task = Task.query.filter_by(name=request.form['task_name']).first()
    task.delete_task()
    db.session.delete(task)
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
        tasks=tasks
    )

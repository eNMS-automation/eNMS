from base.database import db
from flask import Blueprint, render_template, request
from flask_login import login_required
from .forms import CompareGettersForm
from .models import Task, scheduler

blueprint = Blueprint(
    'scheduling_blueprint', 
    __name__, 
    url_prefix = '/scheduling', 
    template_folder = 'templates'
    )

@blueprint.route('/task_management')
@login_required
def task_management():
    tasks = Task.query.all()
    form_per_task = {}
    for task in tasks:
        form = CompareGettersForm(request.form)
        form.first_node.choices = [(i, i) for (i, _, _) in task.nodes]
        form.second_node.choices = form.first_node.choices
        form_per_task[task.name] = form
    return render_template(
        'task_management.html',
        tasks = tasks,
        form_per_task = form_per_task
        )
        
@blueprint.route('/delete_task', methods=['POST'])
@login_required
def delete_task():
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

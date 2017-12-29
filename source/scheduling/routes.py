from base.routes import _render_template
from flask import Blueprint, request
from flask_login import login_required
from .models import Task

blueprint = Blueprint(
    'scheduling_blueprint', 
    __name__, 
    url_prefix = '/scheduling', 
    template_folder = 'templates'
    )

@blueprint.route('/task_management')
@login_required
def task_management():
    for task in Task.query.all():
        print(task.__dict__)
    return _render_template(
        'task_management.html',
        tasks = Task.query.all()
        )
        
@blueprint.route('/delete_task', methods=['POST'])
@login_required
def delete_task():
    Task.query.filter_by(name=request.form['task_name']).delete()
    db.session.commit()
    return index()
    
@blueprint.route('/pause_task', methods=['POST'])
@login_required
def pause_task():
    task = Task.query.filter_by(name=request.form['task_name']).first()
    task.pause_task()
    return index()
    
@blueprint.route('/resume_task', methods=['POST'])
@login_required
def resume_task():
    task = Task.query.filter_by(name=request.form['task_name']).first()
    task.resume_task()
    return index()
    
@blueprint.route('/calendar')
@login_required
def calendar():
    return _render_template('calendar.html')

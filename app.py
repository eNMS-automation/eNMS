from __future__ import print_function
from collections import Counter
from datetime import datetime
from flask import (
    Flask, 
    render_template, 
    request, 
    make_response, 
    jsonify, 
    redirect, 
    url_for
    )
from flask_apscheduler import APScheduler
from flask_sqlalchemy import SQLAlchemy
from inspect import stack
from jinja2 import Template
from os.path import abspath, dirname, join
from subprocess import Popen
from yaml import load
import flask_login
import json
import logging
import os
import sys
import xlrd

# prevent python from writing *.pyc files / __pycache__ folders
sys.dont_write_bytecode = True

path_app = dirname(abspath(stack()[0][1]))
if path_app not in sys.path:
    sys.path.append(path_app)

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
app.database = db

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = join(APP_ROOT, 'uploads')
GETTERS_FOLDER = join(APP_ROOT, 'getters')
APPS_FOLDER = join(APP_ROOT, 'applications')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

from forms import *
from helpers import *
from models import *
from database import *
from users.models import *
from objects.models import *

# start the scheduler
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# start the login system
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

for name in ('users', 'objects', 'views', 'automation', 'scheduling'):
    module = __import__(name + '.routes', globals(), locals(), [''])
    app.register_blueprint(module.blueprint)

# mod = __import__('users.routes', globals(), locals(), [''])
# from users.routes import users_blueprint
# from objects.routes import objects_blueprint
# from views.routes import views_blueprint
# from automation.routes import automation_blueprint
# from scheduling.routes import scheduling_blueprint
# 
# app.register_blueprint(mod.blueprint)
# app.register_blueprint(objects_blueprint)
# app.register_blueprint(views_blueprint)
# app.register_blueprint(automation_blueprint)
# app.register_blueprint(scheduling_blueprint)

# modified template rendering that includes the username as an argument
# it is used by the sidebar as well as the top navigation 
def _render_template(*args, **kwargs):
    try: 
        kwargs['user'] = flask_login.current_user.username
    except AttributeError:
        # 'AnonymousUserMixin' object has no attribute 'username'
        pass
    return render_template(*args, **kwargs)
    
app.render_template = _render_template
    
## Tear down SQLAlchemy 

@app.teardown_request
def shutdown_session(exception=None):
    db.session.remove()
    
## Login / registration

@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'GET':
        form = CreateAccountForm(request.form)
        return _render_template('login/create_account.html', form=form)
    else:
        login_form = LoginForm(request.form)
        user = User(**request.form)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))

@login_manager.user_loader
def user_loader(id):
    return db.session.query(User).filter_by(id=id).first()

@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = db.session.query(User).filter_by(username=username).first()
    return user if user else None

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user = db.session.query(User).filter_by(username=username).first()
        if user and request.form['password'] == user.password:
            flask_login.login_user(user)
            return redirect(url_for('dashboard'))
        return render_template('errors/page_403.html')
    if not flask_login.current_user.is_authenticated:
        login_form = LoginForm(request.form)
        return _render_template('login/login.html', login_form=login_form)
    return redirect(url_for('dashboard'))
        
@app.route('/logout')
def logout():
    flask_login.logout_user()
    return 'Logged out'
    
@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('errors/page_403.html')

## Dashboard
    
@app.route('/dashboard')
@flask_login.login_required
def dashboard():
    # nodes properties
    node_counters = {
        property: 
            Counter(
                map(
                    lambda o: str(getattr(o, property)), 
                    Node.query.all()
                    )
                )
        for property in ('vendor', 'operating_system', 'os_version')
        }
    # link properties
    link_counters = {
        property: 
            Counter(
                map(
                    lambda o: str(getattr(o, property)), 
                    Link.query.all()
                    )
                )
        for property in ('type',)
        }
    return _render_template(
        'home/index.html', 
        node_counters = node_counters,
        link_counters = link_counters
        )
    
@app.route('/ajax_connection_to_node2', methods = ['POST'])
@flask_login.login_required
def ajax_request2():
    id = request.form['id']
    print(id)
    return jsonify(id=id)

@app.route('/ajax_connection_to_node', methods = ['POST'])
@flask_login.login_required
def ajax_request():
    ip_address = request.form['ip_address']
    path_putty = join(APPS_FOLDER, 'putty.exe')
    ssh_connection = '{} -ssh {}'.format(path_putty, ip_address)
    connect = Popen(ssh_connection.split())
    return jsonify(ip_address=ip_address)


## Errors

@app.errorhandler(403)
def not_found_error(error):
    return render_template('errors/page_403.html'), 403

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/page_404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/page_500.html'), 500

## Logs

if not app.debug:
    logging.basicConfig(filename='error.log',level=logging.DEBUG)

if __name__ == '__main__':
    init_db()

    # run flask on port 5100
    port = int(os.environ.get('PORT', 5100))
    
    app.run(host='0.0.0.0', port=port, threaded=True)

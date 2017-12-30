from flask import Flask
from flask_apscheduler import APScheduler
from inspect import stack
from os.path import abspath, dirname, join, pardir
import flask_login
import logging
import os
import sys

# prevent python from writing *.pyc files / __pycache__ folders
sys.dont_write_bytecode = True

path_app = dirname(abspath(stack()[0][1]))
if path_app not in sys.path:
    sys.path.append(path_app)

from base.database import db, init_db
from users.routes import login_manager

def initialize_paths(app):
    path_source = os.path.dirname(os.path.abspath(__file__))
    path_parent = abspath(join(path_source, pardir))
    app.path_upload = join(path_parent, 'uploads')
    app.path_apps = join(path_parent, 'applications')
    app.config['UPLOAD_FOLDER'] = app.path_upload

def start_scheduler(app):
    # start the scheduler
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    return scheduler

def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)

def register_blueprints(app):
    for name in ('base', 'users', 'objects', 'views', 'automation', 'scheduling'):
        module = __import__(name + '.routes', globals(), locals(), [''])
        app.register_blueprint(module.blueprint)

def create_app(config='config'):
    app = Flask(__name__, static_folder='base/static')
    app.config.from_object('config')
    
    initialize_paths(app)
    app.scheduler = start_scheduler(app)
    register_extensions(app)
    register_blueprints(app)

    return app

app = create_app()

from users.models import User

@login_manager.user_loader
def user_loader(id):
    return db.session.query(User).filter_by(id=id).first()

@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = db.session.query(User).filter_by(username=username).first()
    return user if user else None

## tear down SQLAlchemy 

@app.teardown_request
def shutdown_session(exception=None):
    db.session.remove()

## Logs

if not app.debug:
    logging.basicConfig(filename='error.log',level=logging.DEBUG)

if __name__ == '__main__':
    init_db()
    
    # returns logger
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())

    # run flask on port 5100
    port = int(os.environ.get('PORT', 5100))
    app.run(host='0.0.0.0', port=port, threaded=True)

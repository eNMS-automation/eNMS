from flask import Flask
from flask_migrate import Migrate
from importlib import import_module
from inspect import stack
from os.path import abspath, dirname, join, pardir
import logging
import os
import sys

# prevent python from writing *.pyc files / __pycache__ folders
sys.dont_write_bytecode = True

path_app = dirname(abspath(stack()[0][1]))
if path_app not in sys.path:
    sys.path.append(path_app)

path_source = os.path.dirname(os.path.abspath(__file__))
path_parent = abspath(join(path_source, pardir))

from base.database import db, create_database
from tasks.models import scheduler
from users.routes import login_manager

def initialize_paths(app):
    app.path_upload = join(path_parent, 'projects')
    app.path_apps = join(path_parent, 'applications')
    app.kmz_path = join(path_parent, 'kmz')
    app.config['UPLOAD_FOLDER'] = app.path_upload

def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)

def register_blueprints(app):
    blueprints = (
        'base',
        'objects',
        'users',
        'views',
        'tasks'
        )
    for blueprint in blueprints:
        module = import_module('{}.routes'.format(blueprint))
        app.register_blueprint(module.blueprint)

def configure_login_manager(app, User):
    @login_manager.user_loader
    def user_loader(id):
        return db.session.query(User).filter_by(id=id).first()
    
    @login_manager.request_loader
    def request_loader(request):
        username = request.form.get('username')
        user = db.session.query(User).filter_by(username=username).first()
        return user if user else None

def configure_database(app):
    create_database()
    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()
    migrate = Migrate(app, db)

def configure_logs(app):
    logging.basicConfig(filename='error.log',level=logging.DEBUG)
    logger = logging.getLogger('netmiko')
    logger.addHandler(logging.StreamHandler())

def create_app(config='config'):
    app = Flask(__name__, static_folder='base/static')
    app.config.from_object('config')
    
    initialize_paths(app)
    register_extensions(app)
    register_blueprints(app)
    
    from users.models import User
    configure_login_manager(app, User)
    
    configure_database(app)
    configure_logs(app)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(
        host = '0.0.0.0',
        port = int(os.environ.get('PORT', 5100)),
        threaded = True
        )

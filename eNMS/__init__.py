from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from os import environ
from os.path import abspath, dirname, join, pardir
import sys
import logging


db = SQLAlchemy()
login_manager = LoginManager()


from eNMS.admin.models import create_default_parameters, SyslogServer, User
from eNMS.config import config_dict
from eNMS.objects.models import create_default_pools
from eNMS.scripts.custom_scripts import create_custom_scripts
from eNMS.scripts.models import create_default_scripts
from eNMS.tasks.models import scheduler

get_config_mode = environ.get('ENMS_CONFIG_MODE', 'Production')

try:
    config_mode = config_dict[get_config_mode.capitalize()]
except KeyError:
    sys.exit('Error: Invalid ENMS_CONFIG_MODE environment variable entry.')

def initialize_paths(app):
    app.path_upload = join(path_parent, 'projects')
    app.path_apps = join(path_parent, 'applications')
    app.ge_path = join(path_parent, 'google_earth')
    app.path_playbooks = join(path_parent, 'playbooks')
    app.path_file_transfer = join(path_parent, 'file_transfer')
    app.config['UPLOAD_FOLDER'] = app.path_upload


def register_extensions(app, test):
    db.init_app(app)
    login_manager.init_app(app)
    if not test:
        scheduler.init_app(app)


def register_blueprints(app):
    blueprints = (
        'base',
        'objects',
        'scripts',
        'workflows',
        'tasks',
        'admin',
        'views',
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
        name = request.form.get('name')
        user = db.session.query(User).filter_by(name=name).first()
        return user if user else None


def configure_database(app):

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()

    @app.before_first_request
    def create_default():
        create_default_parameters()
        create_default_scripts()
        create_default_pools()
        create_custom_scripts()


def configure_syslog():
    try:
        syslog_server = db.session.query(SyslogServer).one()
        syslog_server.start()
    except Exception:
        pass


def configure_logs(app):
    logging.basicConfig(filename='error.log', level=logging.DEBUG)
    logger = logging.getLogger('netmiko')
    logger.addHandler(logging.StreamHandler())


def configure_scheduler(scheduler):
    scheduler.start()


def create_app(test=False):
    app = Flask(__name__, static_folder='base/static')
    app.config.from_object(config_mode)
    # initialize_paths(app)
    register_extensions(app, test)
    register_blueprints(app)
    configure_login_manager(app, User)
    configure_database(app)
    if not test:
        
        configure_scheduler(scheduler)
    configure_syslog()
    configure_logs(app)
    return app

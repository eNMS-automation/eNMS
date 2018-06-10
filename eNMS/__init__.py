from flask import Flask
from flask_apscheduler import APScheduler
from flask_login import LoginManager

from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from os import environ
from os.path import abspath, dirname, join, pardir
import sys
import logging

sys.dont_write_bytecode = True

db = SQLAlchemy()
login_manager = LoginManager()
scheduler = APScheduler()



from eNMS.objects.models import *
from eNMS.tasks.models import *
from eNMS.workflows.models import *
from eNMS.admin.models import *
from eNMS.base.models import *
from eNMS.scripts.models import *
from eNMS.config import config_dict
from eNMS.scripts.custom_scripts import create_custom_scripts


get_config_mode = environ.get('ENMS_CONFIG_MODE', 'Production')

try:
    config_mode = config_dict[get_config_mode.capitalize()]
except KeyError:
    sys.exit('Error: Invalid ENMS_CONFIG_MODE environment variable entry.')


def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
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
        module = import_module('eNMS.{}'.format(blueprint))
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
        db.create_all()
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


def configure_rest_api(app):
    api = Api(app)
    class RestAutomation(Resource):
    
        def get(self, task_name):
            task = get_obj(Task, name=task_name)
            task.run()
            return {'result': task.serialized}
            
    
    
    api.add_resource(
        RestAutomation,
        '/execute_task/<string:task_name>'
    )



def create_app(path):
    app = Flask(__name__, static_folder='base/static')
    app.config.from_object(config_mode)
    app.path = path
    register_extensions(app)
    register_blueprints(app)
    configure_login_manager(app, User)
    configure_database(app)
    configure_scheduler(scheduler)
    configure_rest_api(app)
    configure_syslog()
    configure_logs(app)
    return app

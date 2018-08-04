from flask import Flask
from flask_apscheduler import APScheduler
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from os import environ
import logging
import sys

# for the tests, we set expire_on_commit to false
db = SQLAlchemy(session_options={"expire_on_commit": False})
login_manager = LoginManager()
scheduler = APScheduler()

import eNMS.objects.models
import eNMS.tasks.models
import eNMS.workflows.models
import eNMS.admin.models
import eNMS.base.models
import eNMS.scripts.models
from eNMS.admin.models import (
    create_default_parameters,
    create_default_syslog_server
)
from eNMS.base.rest import configure_rest_api
from eNMS.config import config_dict
from eNMS.objects.models import create_default_pools
from eNMS.scripts.custom_scripts import create_custom_scripts
from eNMS.scripts.models import create_default_scripts

get_config_mode = environ.get('ENMS_CONFIG_MODE', 'Production')

try:
    config_mode = config_dict[get_config_mode.capitalize()]
except KeyError:
    sys.exit('Error: Invalid ENMS_CONFIG_MODE environment variable entry.')


def register_extensions(app, test):
    db.init_app(app)
    login_manager.init_app(app)
    if not test:
        scheduler.init_app(app)
        scheduler.start()


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


def configure_login_manager(app):
    @login_manager.user_loader
    def user_loader(id):
        return db.session.query(eNMS.admin.models.User).filter_by(id=id).first()

    @login_manager.request_loader
    def request_loader(request):
        name = request.form.get('name')
        user = db.session.query(eNMS.admin.models.User).filter_by(name=name).first()
        return user if user else None


def configure_database(app, test):
    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()

    @app.before_first_request
    def create_default():
        db.create_all()
        create_default_parameters()
        create_default_scripts()
        create_default_pools()
        if not test:
            try:
                create_default_syslog_server()
            except:
                pass
        create_custom_scripts()


def configure_logs(app):
    logging.basicConfig(filename='error.log', level=logging.DEBUG)
    logger = logging.getLogger('netmiko')
    logger.addHandler(logging.StreamHandler())


def create_app(path, test=False, selenium=False):
    app = Flask(__name__, static_folder='base/static')
    if selenium:
        app.config.from_object(config_dict['Selenium'])
    else:
        app.config.from_object(config_mode)
    app.path = path
    register_extensions(app, test)
    register_blueprints(app)
    configure_login_manager(app)
    configure_database(app, test)
    configure_rest_api(app)
    configure_logs(app)
    return app

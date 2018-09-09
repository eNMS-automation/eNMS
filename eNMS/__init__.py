from flask import Flask
from flask_apscheduler import APScheduler
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from hvac import Client as VaultClient
from importlib import import_module
import logging

# for the tests, we set expire_on_commit to false
db = SQLAlchemy(session_options={"expire_on_commit": False})
login_manager = LoginManager()
scheduler = APScheduler()

from eNMS.admin.models import User
from eNMS.base.default import (
    create_default_network_topology,
    create_default_parameters,
    create_default_pools,
    create_default_scripts,
    create_default_tasks,
    create_default_user,
    create_default_workflows
)
from eNMS.base.rest import configure_rest_api
from eNMS.scripts.custom_script import create_custom_scripts


def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    if not scheduler.running:
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
        module = import_module(f'eNMS.{blueprint}')
        app.register_blueprint(module.blueprint)


def configure_login_manager(app):
    @login_manager.user_loader
    def user_loader(id):
        return db.session.query(User).filter_by(id=id).first()

    @login_manager.request_loader
    def request_loader(request):
        name = request.form.get('name')
        user = db.session.query(User).filter_by(name=name).first()
        return user if user else None


def create_vault_client(app):
    return VaultClient(
        url=app.config['VAULT_ADDR'],
        token=app.config['VAULT_TOKEN']
    )


def configure_database(app):
    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()

    @app.before_first_request
    def create_default():
        db.create_all()
        create_default_user()
        create_default_parameters()
        create_default_network_topology(app)
        create_default_pools()
        create_default_scripts()
        create_custom_scripts()
        create_default_tasks()
        create_default_workflows()


def configure_logs(app):
    logging.basicConfig(filename='error.log', level=logging.DEBUG)
    logger = logging.getLogger('netmiko')
    logger.addHandler(logging.StreamHandler())


def create_app(path, config):
    app = Flask(__name__, static_folder='base/static')
    app.config.from_object(config)
    app.production = not app.config['DEBUG']
    app.path = path
    register_extensions(app)
    register_blueprints(app)
    configure_login_manager(app)
    configure_database(app)
    configure_rest_api(app)
    configure_logs(app)
    if app.production:
        app.vault_client = create_vault_client(app)
    return app

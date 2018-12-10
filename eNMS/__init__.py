from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, render_template
from flask_httpauth import HTTPBasicAuth
from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from hvac import Client as VaultClient
from importlib import import_module
from logging import basicConfig, DEBUG, info, StreamHandler
from logging.handlers import RotatingFileHandler
from os import environ
from tacacs_plus.client import TACACSClient

auth = HTTPBasicAuth()
db = SQLAlchemy(
    session_options={
        'expire_on_commit': False,
        'autoflush': False
    }
)
login_manager = LoginManager()
mail = Mail()

# Scheduler
scheduler = BackgroundScheduler({
    'apscheduler.jobstores.default': {
        'type': 'sqlalchemy',
        'url': 'sqlite:///jobs.sqlite'
    },
    'apscheduler.executors.default': {
        'class': 'apscheduler.executors.pool:ThreadPoolExecutor',
        'max_workers': '50'
    },
    'apscheduler.job_defaults.misfire_grace_time': '5',
    'apscheduler.job_defaults.coalesce': 'true',
    'apscheduler.job_defaults.max_instances': '3'
})

# Vault
use_vault = int(environ.get('USE_VAULT', False))
vault_client = VaultClient()

# Tacacs+
use_tacacs = int(environ.get('USE_TACACS', False))
tacacs_client = TACACSClient(
    environ.get('TACACS_ADDR'),
    49,
    environ.get('TACACS_PASSWORD'),
) if use_tacacs else None

# Syslog
use_syslog = int(environ.get('USE_SYSLOG', False))


from eNMS.base.default import (
    create_default_services,
    create_default_parameters,
    create_default_pools,
    create_default_users,
    create_default_examples
)
from eNMS.base.helpers import fetch, get_one
from eNMS.base.rest import configure_rest_api
from eNMS.logs.models import SyslogServer


def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    scheduler.app = app
    if not scheduler.running:
        scheduler.start()


def register_blueprints(app):
    blueprints = (
        'admin',
        'automation',
        'base',
        'logs',
        'objects',
        'scheduling',
        'views'
    )
    for blueprint in blueprints:
        module = import_module(f'eNMS.{blueprint}')
        app.register_blueprint(module.bp)


def configure_login_manager(app):
    @login_manager.user_loader
    def user_loader(id):
        return fetch('User', id=id)

    @login_manager.request_loader
    def request_loader(request):
        return fetch('User', name=request.form.get('name'))


def configure_vault_client(app):
    vault_client.url = app.config['VAULT_ADDR']
    vault_client.token = app.config['VAULT_TOKEN']
    if vault_client.sys.is_sealed() and app.config['UNSEAL_VAULT']:
        keys = [app.config[f'UNSEAL_VAULT_KEY{i}'] for i in range(1, 6)]
        vault_client.sys.submit_unseal_keys(filter(None, keys))


def configure_syslog_server(app):
    server = SyslogServer(
        app.config['SYSLOG_ADDR'],
        app.config['SYSLOG_PORT']
    )
    server.start()


def configure_database(app):
    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()

    @app.before_first_request
    def create_default():
        db.create_all()
        configure_instance_id()
        create_default_users()
        create_default_parameters()
        create_default_services()
        if app.config['CREATE_EXAMPLES']:
            create_default_examples(app)
        create_default_pools()


def configure_errors(app):
    @login_manager.unauthorized_handler
    def unauthorized_handler():
        return render_template('errors/page_403.html'), 403

    @app.errorhandler(403)
    def authorization_required(error):
        return render_template('errors/page_403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/page_404.html'), 404


def configure_logs(app):
    basicConfig(
        level=DEBUG,
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%m-%d-%Y %H:%M:%S',
        handlers=[
            RotatingFileHandler(
                app.path / 'logs' / 'app_logs' / 'enms.log',
                maxBytes=20000000,
                backupCount=10
            ),
            StreamHandler()
        ]
    )


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
    configure_errors(app)
    if use_vault:
        configure_vault_client(app)
    if use_syslog:
        configure_syslog_server(app)
    info('eNMS starting')
    return app

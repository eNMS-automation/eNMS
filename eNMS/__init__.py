from flask import Flask, render_template
from flask_apscheduler import APScheduler
from flask_httpauth import HTTPBasicAuth
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from hvac import Client as VaultClient
from importlib import import_module
from logging import basicConfig, DEBUG, info, StreamHandler
from logging.handlers import RotatingFileHandler

auth = HTTPBasicAuth()
db = SQLAlchemy(
    session_options={
        'expire_on_commit': False,
        'autoflush': False
    }
)
login_manager = LoginManager()
scheduler = APScheduler()

from eNMS.base.models import classes
from eNMS.base.default import (
    create_default_parameters,
    create_default_users,
    create_default_examples
)
from eNMS.base.rest import configure_rest_api


def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    if not scheduler.running:
        scheduler.init_app(app)
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
        return db.session.query(classes['User']).filter_by(id=id).first()

    @login_manager.request_loader
    def request_loader(request):
        name = request.form.get('name')
        user = db.session.query(classes['User']).filter_by(name=name).first()
        return user if user else None


def create_vault_client(app):
    client = VaultClient(
        url=app.config['VAULT_ADDR'],
        token=app.config['VAULT_TOKEN']
    )
    if client.is_sealed() and app.config['UNSEAL_VAULT']:
        keys = [app.config[f'UNSEAL_VAULT_KEY{i}'] for i in range(1, 6)]
        client.unseal_multi(filter(None, keys))
    return client


def configure_database(app):
    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()

    @app.before_first_request
    def create_default():
        db.create_all()
        create_default_users()
        create_default_parameters()
        # create_default_examples(app)


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

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/page_500.html'), 500


def configure_logs(app):
    basicConfig(
        level=DEBUG,
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%m-%d-%Y %H:%M:%S',
        handlers=[
            RotatingFileHandler(
                app.path / 'logs' / 'enms.log',
                maxBytes=2000000,
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
    if app.config['USE_VAULT']:
        app.vault_client = create_vault_client(app)
    info('eNMS starting')
    return app

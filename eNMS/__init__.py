from flask import Flask, render_template
from importlib import import_module
from logging import basicConfig, DEBUG, info, StreamHandler
from logging.handlers import RotatingFileHandler

from eNMS.main import (
    db,
    login_manager,
    mail_client,
    scheduler,
    USE_SYSLOG,
    USE_VAULT,
    vault_client
)
from eNMS.admin.helpers import configure_instance_id
from eNMS.base.default import create_default, create_examples
from eNMS.base.helpers import fetch
from eNMS.base.rest import configure_rest_api
from eNMS.logs.models import SyslogServer


def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    mail_client.init_app(app)
    scheduler.app = app


def register_blueprints(app):
    blueprints = (
        'admin',
        'automation',
        'base',
        'logs',
        'inventory',
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
    def initialize_database():
        db.create_all()
        configure_instance_id()
        create_default(app)
        if app.config['CREATE_EXAMPLES']:
            create_examples(app)
        if not scheduler.running:
            scheduler.start()


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
    if USE_VAULT:
        configure_vault_client(app)
    if USE_SYSLOG:
        configure_syslog_server(app)
    info('eNMS starting')
    return app

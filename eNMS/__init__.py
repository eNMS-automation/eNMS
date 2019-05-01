from flask import Flask, render_template
from flask.wrappers import Request, Response
from flask_cli import FlaskCLI
from importlib import import_module
from importlib.abc import Loader
from importlib.util import spec_from_file_location, module_from_spec
from logging import basicConfig, info, StreamHandler
from logging.handlers import RotatingFileHandler
from os import environ
from pathlib import Path
from simplekml import Color, Style
from sqlalchemy import Boolean, Float, Integer, PickleType
from sqlalchemy.exc import InvalidRequestError
from typing import Any, Optional, Tuple, Type, Union

from eNMS.cli import configure_cli
from eNMS.config import Config
from eNMS.controller import controller
from eNMS.default import create_default
from eNMS.examples import create_examples
from eNMS.forms import form_properties
from eNMS.database import fetch, get_one
from eNMS.modules import (
    bp,
    db,
    login_manager,
    mail_client,
    USE_SYSLOG,
    USE_VAULT,
    vault_client,
)
from eNMS.models import classes, service_classes
from eNMS.models.logging import SyslogServer
from eNMS.models.management import User
from eNMS.properties import (
    boolean_properties,
    cls_to_properties,
    device_subtypes,
    google_earth_styles,
    link_subtypes,
    link_subtype_to_color,
    pretty_names,
    property_types,
    service_import_properties,
)
from eNMS.rest import configure_rest_api


import eNMS.routes


def register_modules(app: Flask) -> None:
    app.register_blueprint(bp)
    db.init_app(app)
    login_manager.init_app(app)
    mail_client.init_app(app)
    FlaskCLI(app)
    controller.init_app(app, db.create_scoped_session())


def configure_login_manager(app: Flask) -> None:
    @login_manager.user_loader
    def user_loader(id: int) -> User:
        return fetch("User", id=id)

    @login_manager.request_loader
    def request_loader(request: Request) -> User:
        return fetch("User", name=request.form.get("name"))


def configure_vault_client(app: Flask) -> None:
    vault_client.url = app.config["VAULT_ADDR"]
    vault_client.token = app.config["VAULT_TOKEN"]
    if vault_client.sys.is_sealed() and app.config["UNSEAL_VAULT"]:
        keys = [app.config[f"UNSEAL_VAULT_KEY{i}"] for i in range(1, 6)]
        vault_client.sys.submit_unseal_keys(filter(None, keys))


def configure_syslog_server(app: Flask) -> None:
    server = SyslogServer(app.config["SYSLOG_ADDR"], app.config["SYSLOG_PORT"])
    server.start()


def configure_database(app: Flask) -> None:
    @app.teardown_request
    def shutdown_session(
        exception: Optional[Union[Response, Exception]] = None
    ) -> None:
        db.session.remove()
        if exception and db.session.is_active:
            db.session.rollback()

    @app.before_first_request
    def initialize_database() -> None:
        db.create_all()
        create_default(app)
        if app.config["CREATE_EXAMPLES"]:
            create_examples(app)


def configure_context_processor(app) -> None:
    @app.context_processor
    def inject_properties():
        return {
            "form_properties": form_properties,
            "names": pretty_names,
            "parameters": get_one("Parameters").serialized,
            "property_types": {k: str(v) for k, v in property_types.items()},
            "services_classes": sorted(service_classes),
        }


def configure_errors(app: Flask) -> None:
    @login_manager.unauthorized_handler
    def unauthorized_handler() -> Tuple[str, int]:
        return render_template("errors/page_403.html"), 403

    @app.errorhandler(403)
    def authorization_required(error: Any) -> Tuple[str, int]:
        return render_template("errors/page_403.html"), 403

    @app.errorhandler(404)
    def not_found_error(error: Any) -> Tuple[str, int]:
        return render_template("errors/page_404.html"), 404


def configure_logs(app: Flask) -> None:
    basicConfig(
        level=getattr(import_module("logging"), app.config["ENMS_LOG_LEVEL"]),
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%m-%d-%Y %H:%M:%S",
        handlers=[
            RotatingFileHandler(
                app.path / "logs" / "app_logs" / "enms.log",
                maxBytes=20_000_000,
                backupCount=10,
            ),
            StreamHandler(),
        ],
    )


def configure_google_earth(path: Path) -> None:
    for subtype in device_subtypes:
        point_style = Style()
        point_style.labelstyle.color = Color.blue
        path_icon = f"{path}/eNMS/views/static/images/2D/{subtype}.gif"
        point_style.iconstyle.icon.href = path_icon
        google_earth_styles[subtype] = point_style
    for subtype in link_subtypes:
        line_style = Style()
        color = link_subtype_to_color[subtype]
        kml_color = "#ff" + color[-2:] + color[3:5] + color[1:3]
        line_style.linestyle.color = kml_color
        google_earth_styles[subtype] = line_style


def configure_services(path: Path) -> None:
    path_services = [path / "eNMS" / "services"]
    custom_services_path = environ.get("CUSTOM_SERVICES_PATH")
    if custom_services_path:
        path_services.append(Path(custom_services_path))
    dont_create_examples = not int(environ.get("CREATE_EXAMPLES", True))
    for path in path_services:
        for file in path.glob("**/*.py"):
            if "init" in str(file):
                continue
            if dont_create_examples and "examples" in str(file):
                continue
            spec = spec_from_file_location(str(file).split("/")[-1][:-3], str(file))
            assert isinstance(spec.loader, Loader)
            module = module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
            except InvalidRequestError:
                continue


def create_app(path: Path, config_class: Type[Config]) -> Flask:
    app = Flask(__name__, static_folder="static")
    app.config.from_object(config_class)  # type: ignore
    app.path = path
    register_modules(app)
    configure_login_manager(app)
    configure_database(app)
    configure_context_processor(app)
    configure_rest_api(app)
    configure_logs(app)
    configure_errors(app)
    configure_google_earth(path)
    configure_services(path)
    configure_cli(app)
    if USE_VAULT:
        configure_vault_client(app)
    if USE_SYSLOG:
        configure_syslog_server(app)
    info("eNMS starting")
    return app

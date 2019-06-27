from flask import Flask, jsonify, make_response, render_template
from flask_assets import Bundle
from flask_cli import FlaskCLI
from flask.wrappers import Request, Response
from pathlib import Path
from sqlalchemy.orm import configure_mappers
from typing import Any, Tuple

from eNMS.cli import configure_cli
from eNMS.config import config_mapper
from eNMS.controller import controller
from eNMS.database import Base, engine
from eNMS.database.events import configure_events
from eNMS.database.functions import fetch
from eNMS.forms import form_properties, property_types
from eNMS.extensions import assets, auth, csrf, login_manager
from eNMS.models.administration import User
from eNMS.properties import property_names
from eNMS.rest import configure_rest_api
from eNMS.routes import blueprint


def register_modules(app: Flask) -> None:
    app.register_blueprint(blueprint)
    assets.init_app(app)
    csrf.init_app(app)
    FlaskCLI(app)
    login_manager.init_app(app)
    controller.init_app(app)


def configure_login_manager(app: Flask) -> None:
    @login_manager.user_loader
    def user_loader(id: int) -> User:
        return fetch("User", allow_none=True, id=id)

    @login_manager.request_loader
    def request_loader(request: Request) -> User:
        return fetch("User", allow_none=True, name=request.form.get("name"))


def configure_database(app: Flask) -> None:
    Base.metadata.create_all(bind=engine)
    configure_mappers()
    configure_events()
    if not fetch("User", allow_none=True, name="admin"):
        controller.init_database()


def configure_context_processor(app: Flask) -> None:
    @app.context_processor
    def inject_properties() -> dict:
        return {
            "form_properties": form_properties,
            "names": property_names,
            "parameters": controller.config,
            "documentation_url": controller.documentation_url,
            "property_types": {k: str(v) for k, v in property_types.items()},
        }


def configure_errors(app: Flask) -> None:
    @login_manager.unauthorized_handler
    def unauthorized_handler() -> Tuple[str, int]:
        return render_template("page_403.html"), 403

    @app.errorhandler(403)
    def authorization_required(error: Any) -> Tuple[str, int]:
        return render_template("page_403.html"), 403

    @app.errorhandler(404)
    def not_found_error(error: Any) -> Tuple[str, int]:
        return render_template("page_404.html"), 404


def configure_assets(app: Flask) -> None:
    assets.register(
        "js", Bundle("lib/base/**/*.js", "base.js", output="bundles/base.js")
    )
    assets.register(
        "css",
        Bundle(
            "lib/base/3_bootstrap/css/bootstrap.min.css",
            "lib/base/**/*.css",
            output="bundles/base.css",
        ),
    )


def configure_authentication() -> None:
    @auth.get_password
    def get_password(username: str) -> str:
        return getattr(fetch("User", name=username), "password", False)

    @auth.error_handler
    def unauthorized() -> Response:
        return make_response(jsonify({"message": "Unauthorized access"}), 403)


def create_app(path: Path, config: str) -> Flask:
    app = Flask(__name__, static_folder="static")
    app.config.from_object(config_mapper[config.capitalize()])  # type: ignore
    app.mode = app.config["MODE"]
    app.path = path
    register_modules(app)
    configure_login_manager(app)
    controller.init_services()
    configure_database(app)
    configure_cli(app)
    configure_context_processor(app)
    configure_rest_api(app)
    configure_errors(app)
    if app.mode != "test":
        configure_assets(app)
    configure_authentication()
    return app

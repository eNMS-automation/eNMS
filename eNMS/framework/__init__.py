from flask import Flask, jsonify, make_response, render_template
from flask.wrappers import Request, Response
from itertools import chain
from typing import Any, Tuple

from eNMS import app
from eNMS.database.functions import fetch
from eNMS.forms import form_properties
from eNMS.framework.cli import configure_cli
from eNMS.framework.config import config_mapper
from eNMS.framework.extensions import auth, csrf, login_manager
from eNMS.framework.rest import configure_rest_api
from eNMS.framework.routes import blueprint
from eNMS.models import relationships
from eNMS.models.administration import User
from eNMS.properties import property_names


def register_extensions(flask_app: Flask) -> None:
    csrf.init_app(flask_app)
    login_manager.init_app(flask_app)


def configure_login_manager() -> None:
    @login_manager.user_loader
    def user_loader(id: int) -> User:
        return fetch("User", allow_none=True, id=id)

    @login_manager.request_loader
    def request_loader(request: Request) -> User:
        return fetch("User", allow_none=True, name=request.form.get("name"))


def configure_context_processor(flask_app: Flask) -> None:
    @flask_app.context_processor
    def inject_properties() -> dict:
        return {
            "documentation_url": app.documentation_url,
            "form_properties": form_properties,
            "names": property_names,
            "parameters": app.config,
            "relations": list(set(chain.from_iterable(relationships.values()))),
            "version": app.version,
        }


def configure_errors(flask_app: Flask) -> None:
    @login_manager.unauthorized_handler
    def unauthorized_handler() -> Tuple[str, int]:
        return render_template("page_403.html"), 403

    @flask_app.errorhandler(403)
    def authorization_required(error: Any) -> Tuple[str, int]:
        return render_template("page_403.html"), 403

    @flask_app.errorhandler(404)
    def not_found_error(error: Any) -> Tuple[str, int]:
        return render_template("page_404.html"), 404


def configure_authentication() -> None:
    @auth.get_password
    def get_password(username: str) -> str:
        return getattr(fetch("User", name=username), "password", False)

    @auth.error_handler
    def unauthorized() -> Response:
        return make_response(jsonify({"message": "Wrong credentials."}), 401)


def create_app() -> Flask:
    flask_app = Flask(__name__, static_folder=app.path / "eNMS" / "static")
    config = config_mapper[app.config_mode.capitalize()]
    flask_app.config.from_object(config)  # type: ignore
    register_extensions(flask_app)
    configure_login_manager()
    configure_cli(flask_app)
    configure_context_processor(flask_app)
    configure_rest_api(flask_app)
    configure_errors(flask_app)
    configure_authentication()
    flask_app.register_blueprint(blueprint)
    return flask_app

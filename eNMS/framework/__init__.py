from flask import Flask, jsonify, make_response, render_template
from flask_login import current_user
from itertools import chain

from eNMS import app
from eNMS.database.functions import fetch
from eNMS.forms import form_properties
from eNMS.framework.cli import configure_cli
from eNMS.framework.config import config_mapper
from eNMS.framework.extensions import auth, csrf, login_manager
from eNMS.framework.rest import configure_rest_api
from eNMS.framework.routes import blueprint
from eNMS.models import models, property_types, relationships
from eNMS.properties import property_names


def register_extensions(flask_app):
    csrf.init_app(flask_app)
    login_manager.init_app(flask_app)


def configure_login_manager():
    @login_manager.user_loader
    def user_loader(id):
        return fetch("user", allow_none=True, id=id)

    @login_manager.request_loader
    def request_loader(request):
        return fetch("user", allow_none=True, name=request.form.get("name"))


def configure_context_processor(flask_app):
    @flask_app.context_processor
    def inject_properties():
        return {
            "property_types": property_types,
            "form_properties": form_properties,
            "names": property_names,
            "config": app.config,
            "relations": list(set(chain.from_iterable(relationships.values()))),
            "relationships": relationships,
            "service_types": {
                service: service_class.pretty_name
                for service, service_class in sorted(models.items())
                if hasattr(service_class, "pretty_name")
            },
            "user": current_user.serialized if current_user.is_authenticated else None,
            "version": app.version,
        }


def configure_errors(flask_app):
    @flask_app.errorhandler(403)
    def authorization_required(error):
        return render_template("error.html", error=403), 403

    @flask_app.errorhandler(404)
    def not_found_error(error):
        return render_template("error.html", error=404), 404


def configure_authentication():
    @auth.get_password
    def get_password(username):
        return getattr(fetch("user", name=username), "password", False)

    @auth.error_handler
    def unauthorized():
        return make_response(jsonify({"message": "Wrong credentials."}), 401)


def create_app(config_mode=None):
    flask_app = Flask(__name__, static_folder=app.path / "eNMS" / "static")
    config = config_mapper[config_mode or app.config["app"]["config_mode"]]
    flask_app.config.from_object(config)
    register_extensions(flask_app)
    configure_login_manager()
    configure_cli(flask_app)
    configure_context_processor(flask_app)
    configure_rest_api(flask_app)
    configure_errors(flask_app)
    configure_authentication()
    flask_app.register_blueprint(blueprint)
    return flask_app

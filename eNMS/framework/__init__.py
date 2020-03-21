from click import argument, echo, option
from json import loads
from passlib.hash import argon2
from flask import abort, Blueprint, Flask, jsonify, make_response, redirect, render_template, request, url_for
from flask_login import current_user
from functools import wraps
from itertools import chain
from logging import info
from os import environ

from eNMS import app
from eNMS.database import Session
from eNMS.database.functions import delete, factory, fetch, handle_exception
from eNMS.forms import form_actions, form_classes, form_postprocessing, form_properties, form_templates
from eNMS.forms.administration import LoginForm
from eNMS.framework.extensions import auth, csrf, login_manager
from eNMS.framework.rest import configure_rest_api
from eNMS.models import models, property_types, relationships
from eNMS.database.properties import property_names
from eNMS.setup import properties, rbac


class WebApplication(Flask):

    def __init__(self, mode=None):
        super().__init__(__name__, static_folder=app.path / "eNMS" / "static")
        self.update_config(mode)
        self.register_extensions()
        self.configure_login_manager()
        self.configure_cli()
        self.configure_context_processor()
        configure_rest_api(self)
        self.configure_errors()
        self.configure_authentication()
        self.configure_routes()

    def configure_routes(self):
        blueprint = Blueprint("blueprint", __name__, template_folder="../templates")

        @blueprint.route("/")
        def site_root():
            return redirect(url_for("blueprint.route", page="login"))

        @blueprint.route("/login", methods=["GET", "POST"])
        def login():
            if request.method == "POST":
                try:
                    user = app.authenticate_user(**request.form.to_dict())
                    if user:
                        login_user(user)
                        return redirect(url_for("blueprint.route", page="dashboard"))
                    else:
                        abort(403)
                except Exception as exc:
                    info(f"Authentication failed ({str(exc)})")
                    abort(403)
            if not current_user.is_authenticated:
                login_form = LoginForm(request.form)
                authentication_methods = []
                if app.settings["ldap"]["active"]:
                    authentication_methods.append(("LDAP Domain",) * 2)
                if app.settings["tacacs"]["active"]:
                    authentication_methods.append(("TACACS",) * 2)
                authentication_methods.append(("Local User",) * 2)
                login_form.authentication_method.choices = authentication_methods
                return render_template("login.html", login_form=login_form)
            return redirect(url_for("blueprint.route", page="dashboard"))

        @blueprint.route("/dashboard")
        @self.monitor_requests
        def dashboard():
            return render_template(
                f"dashboard.html",
                **{"endpoint": "dashboard", "properties": properties["dashboard"]},
            )

        @blueprint.route("/", methods=["POST"])
        @blueprint.route("/<path:page>", methods=["POST"])
        @self.monitor_requests
        def route(page):
            endpoint, *args = page.split("/")
            if f"/{endpoint}" not in app.rbac["endpoints"]["POST"]:
                return jsonify({"alert": "Invalid POST request."})
            if f"/{endpoint}" in app.rbac["groups"][current_user.group]["POST"]:
                return jsonify({"alert": "Error 403 Forbidden."})
            form_type = request.form.get("form_type")
            if endpoint in app.json_endpoints:
                result = getattr(app, endpoint)(*args, **request.json)
            elif form_type:
                form = form_classes[form_type](request.form)
                if not form.validate_on_submit():
                    return jsonify({"invalid_form": True, **{"errors": form.errors}})
                result = getattr(app, endpoint)(
                    *args, **form_postprocessing(form, request.form)
                )
            else:
                result = getattr(app, endpoint)(*args, **request.form)
            try:
                Session.commit()
                return jsonify(result)
            except Exception as exc:
                raise exc
                Session.rollback()
                if app.settings["app"]["config_mode"] == "debug":
                    raise
                return jsonify({"alert": handle_exception(str(exc))})

        self.register_blueprint(blueprint)

    @staticmethod
    def monitor_requests(function):
        @wraps(function)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                client_address = request.environ.get(
                    "HTTP_X_FORWARDED_FOR", request.environ["REMOTE_ADDR"]
                )
                app.log(
                    "warning",
                    (
                        f"Unauthorized {request.method} request from "
                        f"'{client_address}' calling the endpoint '{request.url}'"
                    ),
                )
                return redirect(url_for("blueprint.route", page="login"))
            else:
                forbidden_endpoints = app.rbac["groups"][current_user.group]["GET"]
                if request.method == "GET" and request.path in forbidden_endpoints:
                    return render_template("error.html", error=403), 403
                return function(*args, **kwargs)

        return decorated_function

    def update_config(self, mode):
        mode = (mode or app.settings["app"]["config_mode"]).lower()
        self.config.update({
            "DEBUG": mode != "production",
            "SECRET_KEY": environ.get("SECRET_KEY", "get-a-real-key"),
            "WTF_CSRF_TIME_LIMIT": None,
            "ERROR_404_HELP": False,
            "MAX_CONTENT_LENGTH": 20 * 1024 * 1024,
            "WTF_CSRF_ENABLED": mode != "test",
        })

    def register_extensions(self):
        csrf.init_app(self)
        login_manager.init_app(self)

    def configure_cli(self):
        @self.cli.command(name="fetch")
        @argument("table")
        @argument("name")
        def cli_fetch(table, name):
            echo(
                app.str_dict(fetch(table, name=name).get_properties(exclude=["positions"]))
            )

        @self.cli.command()
        @argument("table")
        @argument("properties")
        def update(table, properties):
            result = factory(table, **loads(properties)).get_properties(
                exclude=["positions"]
            )
            Session.commit()
            echo(app.str_dict(result))

        @self.cli.command(name="delete")
        @argument("table")
        @argument("name")
        def cli_delete(table, name):
            device = delete(table, name=name)
            Session.commit()
            echo(app.str_dict(device))

        @self.cli.command(name="run_service")
        @argument("name")
        @option("--devices")
        @option("--payload")
        def start(name, devices, payload):
            devices_list = devices.split(",") if devices else []
            devices_list = [fetch("device", name=name).id for name in devices_list]
            payload_dict = loads(payload) if payload else {}
            payload_dict["devices"] = devices_list
            service = fetch("service", name=name)
            results = app.run(service.id, **payload_dict)
            Session.commit()
            echo(app.str_dict(results))

    def configure_login_manager(self):
        @login_manager.user_loader
        def user_loader(id):
            return fetch("user", allow_none=True, id=int(id))

        @login_manager.request_loader
        def request_loader(request):
            return fetch("user", allow_none=True, name=request.form.get("name"))


    def configure_context_processor(self):
        @self.context_processor
        def inject_properties():
            return {
                "property_types": property_types,
                "form_properties": form_properties,
                "menu": rbac["menu"],
                "names": property_names,
                "rbac": rbac["groups"][getattr(current_user, "group", "Read Only")],
                "relations": list(set(chain.from_iterable(relationships.values()))),
                "relationships": relationships,
                "service_types": {
                    service: service_class.pretty_name
                    for service, service_class in sorted(models.items())
                    if hasattr(service_class, "pretty_name")
                },
                "settings": app.settings,
                "table_properties": app.properties["tables"],
                "user": current_user.serialized if current_user.is_authenticated else None,
                "version": app.version,
            }


    def configure_errors(self):
        @self.errorhandler(403)
        def authorization_required(error):
            return render_template("error.html", error=403), 403

        @self.errorhandler(404)
        def not_found_error(error):
            return render_template("error.html", error=404), 404


    def configure_authentication(self):
        @auth.verify_password
        def verify_password(username, password):
            user = fetch("user", name=username)
            hash = app.settings["security"]["hash_user_passwords"]
            verify = argon2.verify if hash else str.__eq__
            return verify(password, user.password)

        @auth.get_password
        def get_password(username):
            return getattr(fetch("user", name=username), "password", False)

        @auth.error_handler
        def unauthorized():
            return make_response(jsonify({"message": "Wrong credentials."}), 401)


web_app = WebApplication()

from datetime import datetime, timedelta
from flask import (
    abort,
    Blueprint,
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
    session,
)
from flask_login import current_user, LoginManager, login_user, logout_user, login_url
from flask_wtf.csrf import CSRFProtect
from functools import wraps
from importlib import import_module
from io import BytesIO
from logging import info
from os import getenv, remove
from pathlib import Path
from tarfile import open as open_tar
from traceback import format_exc
from werkzeug.exceptions import Forbidden, NotFound

from eNMS import controller
from eNMS.database import db
from eNMS.environment import env
from eNMS.forms import form_factory
from eNMS.rest_api import RestApi
from eNMS.variables import vs


class Server(Flask):

    status_log_level = {
        200: "info",
        401: "warning",
        403: "warning",
        404: "info",
        500: "error",
    }

    status_error_message = {
        401: "Wrong Credentials.",
        403: "Not Authorized.",
        404: "Not Found.",
        500: "Internal Server Error.",
    }

    def __init__(self):
        static_folder = str(vs.path / "eNMS" / "static")
        super().__init__(__name__, static_folder=static_folder)
        self.rest_api = RestApi()
        self.update_config()
        self.register_extensions()
        self.configure_login_manager()
        self.configure_context_processor()
        self.configure_errors()
        self.configure_routes()

    def update_config(self):
        session_timeout = vs.settings["app"]["session_timeout_minutes"]
        self.config.update(
            {
                "DEBUG": vs.settings["app"]["config_mode"].lower() != "production",
                "SECRET_KEY": getenv("SECRET_KEY", "secret_key"),
                "WTF_CSRF_TIME_LIMIT": None,
                "ERROR_404_HELP": False,
                "MAX_CONTENT_LENGTH": vs.settings["app"]["max_content_length"],
                "PERMANENT_SESSION_LIFETIME": timedelta(minutes=session_timeout),
            }
        )

    def register_plugins(self):
        for plugin, settings in vs.plugins_settings.items():
            try:
                module = import_module(f"eNMS.plugins.{plugin}")
                module.Plugin(self, controller, db, vs, env, **settings)
            except Exception:
                env.log("error", f"Could not import plugin '{plugin}':\n{format_exc()}")
                continue
            info(f"Loading plugin: {settings['name']}")

    def register_extensions(self):
        self.csrf = CSRFProtect()
        self.csrf.init_app(self)

    def configure_login_manager(self):
        login_manager = LoginManager()
        login_manager.session_protection = "strong"
        login_manager.init_app(self)

        @login_manager.user_loader
        def user_loader(name):
            return db.fetch("user", allow_none=True, name=name)

    def configure_context_processor(self):
        @self.context_processor
        def inject_properties():
            return {
                "user": current_user.get_properties()
                if current_user.is_authenticated
                else None,
                "time": str(vs.get_time()),
                "parameters": db.fetch("parameters").serialized,
                **vs.template_context,
            }

    def configure_errors(self):
        @self.errorhandler(403)
        def authorization_required(error):
            login_url = url_for("blueprint.route", page="login")
            return render_template("error.html", error=403, login_url=login_url), 403

        @self.errorhandler(404)
        def not_found_error(error):
            return render_template("error.html", error=404), 404

    @staticmethod
    def process_requests(function):
        @wraps(function)
        def decorated_function(*args, **kwargs):
            time_before = datetime.now()
            remote_address = request.environ["REMOTE_ADDR"]
            client_address = request.environ.get("HTTP_X_FORWARDED_FOR", remote_address)
            rest_request = request.path.startswith("/rest/")
            endpoint = "/".join(request.path.split("/")[: 2 + rest_request])
            request_property = f"{request.method.lower()}_requests"
            endpoint_rbac = vs.rbac[request_property].get(endpoint)
            if rest_request:
                user = None
                if request.authorization:
                    user = env.authenticate_user(**request.authorization)
                if user:
                    login_user(user)
            username = getattr(current_user, "name", "Unknown")
            if not endpoint_rbac:
                status_code = 404
            elif rest_request and endpoint_rbac != "none" and not user:
                status_code = 401
            elif (
                endpoint_rbac != "none"
                and not getattr(current_user, "is_admin", False)
                and (
                    not current_user.is_authenticated
                    or endpoint_rbac == "admin"
                    or (
                        endpoint_rbac == "access"
                        and endpoint not in getattr(current_user, request_property)
                    )
                )
            ):
                status_code = 403
            else:
                try:
                    result = function(*args, **kwargs)
                    status_code = 200
                except (db.rbac_error, Forbidden):
                    status_code = 403
                except NotFound:
                    status_code = 404
                except Exception:
                    status_code, traceback = 500, format_exc()
            time_difference = (datetime.now() - time_before).total_seconds()
            log = (
                f"USER: {username} ({client_address}) - {time_difference:.3f}s - "
                f"{request.method} {request.path} ({status_code})"
            )
            if status_code == 500:
                log += f"\n{traceback}"
            env.log(Server.status_log_level[status_code], log, change_log=False)
            if rest_request:
                logout_user()
            if status_code == 200:
                return result
            elif endpoint == "/login" or request.method == "GET" and not rest_request:
                if (
                    not current_user.is_authenticated
                    and not rest_request
                    and endpoint != "/login"
                ):
                    url = url_for("blueprint.route", page="login", next_url=request.url)
                    return redirect(login_url(url))
                next_url = request.args.get("next_url")
                login_link = login_url(
                    url_for("blueprint.route", page="login", next_url=next_url)
                )
                return (
                    render_template(
                        "error.html", error=status_code, login_url=login_link
                    ),
                    status_code,
                )
            else:
                error_message = Server.status_error_message[status_code]
                alert = f"Error {status_code} - {error_message}"
                return jsonify({"alert": alert}), status_code

        return decorated_function

    def configure_routes(self):
        blueprint = Blueprint("blueprint", __name__, template_folder="../templates")

        @blueprint.route("/")
        @self.process_requests
        def site_root():
            return redirect(url_for("blueprint.route", page="login"))

        @blueprint.route("/login", methods=["GET", "POST"])
        @self.process_requests
        def login():
            if request.method == "POST":
                kwargs, success = request.form.to_dict(), False
                username = kwargs["username"]
                try:
                    user = env.authenticate_user(**kwargs)
                    if user:
                        login_user(user, remember=False)
                        session.permanent = True
                        success, log = True, f"USER '{username}' logged in"
                    else:
                        log = f"Authentication failed for user '{username}'"
                except Exception:
                    log = f"Authentication error for user '{username}' ({format_exc()})"
                finally:
                    env.log("info" if success else "warning", log, logger="security")
                    if success:
                        url = url_for("blueprint.route", page=current_user.landing_page)
                        return redirect(request.args.get("next_url", url))
                    else:
                        abort(403)
            if not current_user.is_authenticated:
                login_form = vs.form_class["login"](request.form)
                return render_template("login.html", login_form=login_form)
            return redirect(url_for("blueprint.route", page=current_user.landing_page))

        @blueprint.route("/dashboard")
        @self.process_requests
        def dashboard():
            return render_template(
                "dashboard.html",
                **{"endpoint": "dashboard", "properties": vs.properties["dashboard"]},
            )

        @blueprint.route("/logout")
        @self.process_requests
        def logout():
            logout_log = f"USER '{current_user.name}' logged out"
            logout_user()
            env.log("info", logout_log, logger="security")
            return redirect(url_for("blueprint.route", page="login"))

        @blueprint.route("/<table_type>_table")
        @self.process_requests
        def table(table_type):
            return render_template(
                "table.html", **{"endpoint": f"{table_type}_table", "type": table_type}
            )

        @blueprint.route("/geographical_view")
        @self.process_requests
        def visualization():
            return render_template("visualization.html", endpoint="geographical_view")

        @blueprint.route("/<type>_builder")
        @blueprint.route("/<type>_builder/<link_path>")
        @blueprint.route("/<type>_builder/<link_path>/<link_runtime>")
        @self.process_requests
        def builder(type, **kwargs):
            endpoint = f"{type}_builder"
            return render_template(f"{endpoint}.html", endpoint=endpoint, **kwargs)

        @blueprint.route("/<form_type>_form")
        @self.process_requests
        def form(form_type):
            form = vs.form_class[form_type](request.form)
            return render_template(
                f"forms/{getattr(form, 'template', 'base')}.html",
                **{
                    "endpoint": f"forms/{form_type}",
                    "action": getattr(form, "action", None),
                    "button_label": getattr(form, "button_label", "Confirm"),
                    "button_class": getattr(form, "button_class", "success"),
                    "form": form,
                    "form_type": form_type,
                },
            )

        @blueprint.route("/parameterized_form/<service_id>")
        @self.process_requests
        def parameterized_form(service_id):
            result = form_factory.register_parameterized_form(service_id)
            if isinstance(result, str):
                return result
            return render_template(
                "forms/base.html",
                **{
                    "form_type": f"initial-{service_id}",
                    "action": "eNMS.automation.submitInitialForm",
                    "button_label": "Run Service",
                    "button_class": "primary",
                    "form": result(request.form),
                },
            )

        @blueprint.route("/help/<path:path>")
        @self.process_requests
        def help(path):
            return render_template(f"help/{path}.html")

        @blueprint.route("/view_service_results/<int:run_id>/<int:service>")
        @self.process_requests
        def view_service_results(run_id, service):
            results = db.fetch_all("result", run_id=run_id, service_id=service)
            results_dict = [result.result for result in results]
            if not results_dict:
                return "No Results Found"
            return f"<pre>{vs.dict_to_string(results_dict)}</pre>"

        @blueprint.route("/download/<type>/<path:path>")
        @self.process_requests
        def download(type, path):
            return_data, path = BytesIO(), f"/{path}"
            if type == "folder":
                with open_tar(f"{path}.tgz", "w:gz") as tar:
                    tar.add(path, arcname="")
                path = f"{path}.tgz"
            with open(path, "rb") as file:
                return_data.write(file.read())
            return_data.seek(0)
            if type == "folder":
                remove(path)
                archive = db.fetch("folder", path=path, allow_none=True)
                if archive:
                    db.session.delete(archive)
            return send_file(return_data, download_name=Path(path).name)

        @blueprint.route("/export_service/<int:id>")
        @self.process_requests
        def export_service(id):
            filename = f"/{controller.export_service(id)}.tgz"
            return send_file(filename, as_attachment=True)

        @blueprint.route("/terminal/<session>")
        @self.process_requests
        def ssh_connection(session):
            return render_template("terminal.html", session=session)

        @blueprint.route("/<path:_>")
        @self.process_requests
        def get_requests_sink(_):
            abort(404)

        @blueprint.route("/rest/<path:page>", methods=["DELETE", "GET", "POST"])
        @self.process_requests
        @self.csrf.exempt
        def rest_request(page):
            method, (endpoint, *args) = request.method, page.split("/")
            if method == "POST":
                kwargs = {**request.form.to_dict(), **request.files.to_dict()}
                payload = request.json if request.data else {}
                if isinstance(payload, list):
                    kwargs["list_data"] = payload
                else:
                    kwargs.update(payload or {})
            else:
                kwargs = request.args.to_dict()
            with db.session_scope():
                endpoint = self.rest_api.rest_endpoints[method][endpoint]
                return jsonify(getattr(self.rest_api, endpoint)(*args, **kwargs))

        @blueprint.route("/", methods=["POST"])
        @blueprint.route("/<path:page>", methods=["POST"])
        @self.process_requests
        def route(page):
            form_type = request.form.get("form_type")
            endpoint, *args = page.split("/")
            if request.is_json:
                kwargs = request.json
            elif form_type:
                if form_type.startswith("initial-") and form_type not in vs.form_class:
                    form_factory.register_parameterized_form(form_type.split("-")[1])
                form = vs.form_class[form_type](request.form)
                if not form.validate_on_submit():
                    return jsonify({"invalid_form": True, "errors": form.errors})
                kwargs = form.form_postprocessing(request.form)
            else:
                kwargs = request.form
            with db.session_scope():
                return jsonify(getattr(controller, endpoint)(*args, **kwargs))

        self.register_blueprint(blueprint)


server = Server()

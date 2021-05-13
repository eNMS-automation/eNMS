from collections import defaultdict
from datetime import timedelta
from flask import (
    abort,
    Blueprint,
    Flask,
    g,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
    session,
)
from flask_httpauth import HTTPBasicAuth
from flask_login import current_user, LoginManager, login_user, logout_user
from flask_login.utils import login_url
from flask_restful import abort as rest_abort, Api, Resource
from flask_wtf.csrf import CSRFProtect
from functools import wraps
from itertools import chain
from os import getenv
from threading import Thread
from time import sleep
from traceback import format_exc
from uuid import getnode

from eNMS import app
from eNMS.database import db
from eNMS.forms import form_classes, form_properties
from eNMS.forms.administration import LoginForm
from eNMS.models import models, property_types, relationships
from eNMS.setup import properties, themes, visualization


class Server(Flask):
    def __init__(self, mode=None):
        static_folder = str(app.path / "eNMS" / "static")
        super().__init__(__name__, static_folder=static_folder)
        self.update_config(mode)
        self.register_extensions()
        self.register_plugins()
        self.configure_login_manager()
        self.configure_context_processor()
        self.configure_errors()
        self.configure_authentication()
        self.configure_routes()
        self.configure_rest_api()

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
                return redirect(login_url(url_for("blueprint.route", page="login"), next_url=request.url))
            else:
                method = request.method.lower()
                endpoint = f"/{request.path.split('/')[1]}"
                endpoint_rbac = app.rbac[f"{method}_requests"].get(endpoint)
                if not endpoint_rbac:
                    error = 404
                elif not current_user.is_admin and (
                    endpoint_rbac == "admin"
                    or endpoint_rbac == "access"
                    and endpoint not in getattr(current_user, f"{method}_requests")
                ):
                    error = 403
                else:
                    try:
                        return function(*args, **kwargs)
                    except db.rbac_error:
                        error = 403
                    except Exception:
                        error = 500
                        app.log("error", format_exc(), change_log=False)
                if method == "get":
                    return render_template("error.html", error=error), error
                else:
                    message = {
                        403: "Operation not allowed.",
                        404: "Invalid POST request.",
                        500: "Internal Server Error.",
                    }[error]
                    return jsonify({"alert": f"Error {error} - {message}"})

        return decorated_function

    def update_config(self, mode):
        mode = (mode or app.settings["app"]["config_mode"]).lower()
        self.config.update(
            {
                "DEBUG": mode != "production",
                "SECRET_KEY": getenv("SECRET_KEY", "secret_key"),
                "WTF_CSRF_TIME_LIMIT": None,
                "ERROR_404_HELP": False,
                "MAX_CONTENT_LENGTH": 20 * 1024 * 1024,
                "WTF_CSRF_ENABLED": mode != "test",
                "PERMANENT_SESSION_LIFETIME": timedelta(
                    minutes=app.settings["app"]["session_timeout_minutes"]
                ),
            }
        )

    def register_plugins(self):
        for plugin in app.plugins.values():
            plugin["module"].Plugin(self, app, db, **plugin["settings"])

    def register_extensions(self):
        self.auth = HTTPBasicAuth()
        self.csrf = CSRFProtect()
        self.csrf.init_app(self)

    def configure_login_manager(self):
        login_manager = LoginManager()
        login_manager.login_view = "blueprint.login"
        login_manager.session_protection = "strong"
        login_manager.init_app(self)

        @login_manager.user_loader
        def user_loader(name):
            return db.get_user(name)

    def configure_context_processor(self):
        @self.context_processor
        def inject_properties():
            return {
                "configuration_properties": app.configuration_properties,
                "form_properties": form_properties,
                "rbac": app.rbac,
                "names": app.property_names,
                "property_types": property_types,
                "relations": list(set(chain.from_iterable(relationships.values()))),
                "relationships": relationships,
                "service_types": {
                    service: service_class.pretty_name
                    for service, service_class in sorted(models.items())
                    if hasattr(service_class, "pretty_name")
                },
                "settings": app.settings,
                "themes": themes,
                "table_properties": app.properties["tables"],
                "user": current_user.serialized
                if current_user.is_authenticated
                else None,
                "version": app.version,
                "visualization": visualization,
            }

    def configure_errors(self):
        @self.errorhandler(403)
        def authorization_required(error):
            return render_template("error.html", error=403), 403

        @self.errorhandler(404)
        def not_found_error(error):
            return render_template("error.html", error=404), 404

    def configure_authentication(self):
        @self.auth.verify_password
        def verify_password(username, password):
            user = app.authenticate_user(name=username, password=password)
            if user:
                request_type = f"{request.method.lower()}_requests"
                endpoint = "/".join(request.path.split("/")[:3])
                if user.is_admin or endpoint in getattr(user, request_type, []):
                    login_user(user)
                    return True
                g.status = 403
            else:
                g.status = 401

        @self.auth.get_password
        def get_password(username):
            return getattr(db.get_user(username), "password", False)

        @self.auth.error_handler
        def unauthorized():
            message = f"{'Wrong' if g.status == 401 else 'Insufficient'} credentials"
            return make_response(jsonify({"message": message}), g.status)

    def configure_routes(self):
        blueprint = Blueprint("blueprint", __name__, template_folder="../templates")

        def redirect_after_login(default=None):
            def is_safe_url(target):
                endpoint = f"/{target.split('/')[1]}"
                endpoint_rbac = app.rbac["get_requests"].get(endpoint)
                return endpoint_rbac and current_user.is_admin or \
                       endpoint_rbac == "access" and \
                       endpoint in getattr(current_user, "get_requests")

            next_url = (request.args.get('next') or '').strip()
            return redirect(next_url if next_url and is_safe_url(next_url) else default)

        @blueprint.route("/")
        def site_root():
            return redirect(url_for("blueprint.route", page="login"))

        @blueprint.route("/login", methods=["GET", "POST"])
        def login():
            if request.method == "POST":
                kwargs, success = request.form.to_dict(), False
                username = kwargs["name"]
                try:
                    user = app.authenticate_user(**kwargs)
                    if user:
                        login_user(user, remember=False)
                        session.permanent = True
                        success, log = True, f"User '{username}' logged in"
                    else:
                        log = f"Authentication failed for user '{username}'"
                except Exception:
                    log = f"Authentication error for user '{username}' ({format_exc()})"
                finally:
                    app.log("info" if success else "warning", log, logger="security")
                    if success:
                        return redirect_after_login(default=url_for("blueprint.route", page="dashboard"))
                    else:
                        abort(403)
            if not current_user.is_authenticated:
                login_form = LoginForm(request.form)
                methods = app.settings["authentication"]["methods"].items()
                login_form.authentication_method.choices = [
                    (method, properties["display_name"])
                    for method, properties in methods
                    if properties["enabled"]
                ]
                return render_template("login.html", login_form=login_form)
            return redirect(url_for("blueprint.route", page="dashboard"))

        @blueprint.route("/dashboard")
        @self.monitor_requests
        def dashboard():
            return render_template(
                "dashboard.html",
                **{"endpoint": "dashboard", "properties": properties["dashboard"]},
            )

        @blueprint.route("/logout")
        @self.monitor_requests
        def logout():
            logout_log = f"User '{current_user.name}' logging out"
            app.log("info", logout_log, logger="security")
            logout_user()
            return redirect(url_for("blueprint.route", page="login"))

        @blueprint.route("/<table_type>_table")
        @self.monitor_requests
        def table(table_type):
            return render_template(
                "table.html", **{"endpoint": f"{table_type}_table", "type": table_type}
            )

        @blueprint.route("/<view_type>_view")
        @self.monitor_requests
        def view(view_type):
            return render_template(
                "visualization.html",
                endpoint=f"{view_type}_view",
                default_pools=app.get_visualization_parameters(),
            )

        @blueprint.route("/workflow_builder")
        @self.monitor_requests
        def workflow_builder():
            return render_template("workflow.html", endpoint="workflow_builder")

        @blueprint.route("/<form_type>_form")
        @self.monitor_requests
        def form(form_type):
            form = form_classes[form_type](request.form)
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

        @blueprint.route("/help/<path:path>")
        @self.monitor_requests
        def help(path):
            return render_template(f"help/{path}.html")

        @blueprint.route("/view_service_results/<int:id>")
        @self.monitor_requests
        def view_service_results(id):
            result = db.fetch("run", id=id).result(main=True).result
            return f"<pre>{app.str_dict(result)}</pre>"

        @blueprint.route("/download_file/<path:path>")
        @self.monitor_requests
        def download_file(path):
            return send_file(f"/{path}", as_attachment=True)

        @blueprint.route("/export_service/<int:id>")
        @self.monitor_requests
        def export_service(id):
            return send_file(f"/{app.export_service(id)}.tgz", as_attachment=True)

        @blueprint.route("/<path:_>")
        @self.monitor_requests
        def get_requests_sink(_):
            abort(404)

        @blueprint.route("/", methods=["POST"])
        @blueprint.route("/<path:page>", methods=["POST"])
        @self.monitor_requests
        def route(page):
            form_type = request.form.get("form_type")
            endpoint, *args = page.split("/")
            if request.json:
                kwargs = request.json
            elif form_type:
                form = form_classes[form_type](request.form)
                if not form.validate_on_submit():
                    return jsonify({"invalid_form": True, **{"errors": form.errors}})
                kwargs = form.form_postprocessing(request.form)
            else:
                kwargs = request.form
            with db.session_scope():
                return jsonify(getattr(app, endpoint)(*args, **kwargs))

        self.register_blueprint(blueprint)

    @staticmethod
    def monitor_rest_request(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for index in range(db.retry_commit_number):
                try:
                    result = func(*args, **kwargs)
                except db.rbac_error as exc:
                    return rest_abort(404, message=str(exc))
                except Exception as exc:
                    return rest_abort(500, message=str(exc))
                try:
                    db.session.commit()
                    return result
                except Exception as exc:
                    db.session.rollback()
                    app.log("error", f"Rest Call n°{index} failed ({exc}).")
                    stacktrace = format_exc()
                    sleep(db.retry_commit_time * (index + 1))
            else:
                rest_abort(500, message=stacktrace)

        return wrapper

    def configure_rest_api(self):

        api = Api(self, decorators=[self.csrf.exempt])

        class Heartbeat(Resource):
            def get(self):
                return {
                    "name": getnode(),
                    "cluster_id": app.settings["cluster"]["id"],
                }

        class Query(Resource):
            decorators = [self.auth.login_required, self.monitor_rest_request]

            def get(self, model):
                properties = request.args.to_dict()
                results = db.fetch(model, all_matches=True, **properties)
                return [
                    result.get_properties(exclude=["positions"]) for result in results
                ]

        class GetInstance(Resource):
            decorators = [self.auth.login_required, self.monitor_rest_request]

            def get(self, model, name):
                return db.fetch(model, name=name).to_dict(
                    relation_names_only=True, exclude=["positions"]
                )

            def delete(self, model, name):
                result = db.delete(model, name=name)
                return result

        class GetConfiguration(Resource):
            decorators = [self.auth.login_required, self.monitor_rest_request]

            def get(self, name):
                property = request.args.to_dict().get("property", "configuration")
                return getattr(db.fetch("device", name=name), property)

        class GetResult(Resource):
            decorators = [self.auth.login_required, self.monitor_rest_request]

            def get(self, name, runtime):
                run = db.fetch(
                    "run", service_name=name, runtime=runtime, allow_none=True
                )
                if not run:
                    error_message = (
                        "There are no results or on-going services "
                        "for the requested service and runtime."
                    )
                    return {"error": error_message}
                else:
                    result = run.result()
                    return {
                        "status": run.status,
                        "result": result.result if result else "No results yet.",
                    }

        class UpdateInstance(Resource):
            decorators = [self.auth.login_required, self.monitor_rest_request]

            def post(self, model):
                data, result = request.get_json(force=True), defaultdict(list)
                if not isinstance(data, list):
                    data = [data]
                for instance in data:
                    if "name" not in instance:
                        result["failure"].append((instance, "Name is missing"))
                        continue
                    try:
                        object_data = app.objectify(model, instance)
                        object_data["update_pools"] = instance.get("update_pools", True)
                        instance = db.factory(model, **object_data)
                        result["success"].append(instance.name)
                    except Exception:
                        result["failure"].append((instance, format_exc()))
                return result

        class Migrate(Resource):
            decorators = [self.auth.login_required, self.monitor_rest_request]

            def post(self, direction):
                kwargs = request.get_json(force=True)
                return getattr(app, f"migration_{direction}")(**kwargs)

        class RunService(Resource):
            decorators = [self.auth.login_required, self.monitor_rest_request]

            def post(self):
                data = {
                    "trigger": "REST",
                    "creator": request.authorization["username"],
                    **request.get_json(force=True),
                }
                errors, devices, pools = [], [], []
                service = db.fetch("service", name=data["name"], rbac="run")
                handle_asynchronously = data.get("async", False)
                for device_name in data.get("devices", ""):
                    device = db.fetch("device", name=device_name)
                    if device:
                        devices.append(device.id)
                    else:
                        errors.append(f"No device with the name '{device_name}'")
                for device_ip in data.get("ip_addresses", ""):
                    device = db.fetch("device", ip_address=device_ip)
                    if device:
                        devices.append(device.id)
                    else:
                        errors.append(f"No device with the IP address '{device_ip}'")
                for pool_name in data.get("pools", ""):
                    pool = db.fetch("pool", name=pool_name)
                    if pool:
                        pools.append(pool.id)
                    else:
                        errors.append(f"No pool with the name '{pool_name}'")
                if errors:
                    return {"errors": errors}
                if devices or pools:
                    data.update({"target_devices": devices, "target_pools": pools})
                data["runtime"] = runtime = app.get_time()
                if handle_asynchronously:
                    Thread(target=app.run, args=(service.id,), kwargs=data).start()
                    return {"errors": errors, "runtime": runtime}
                else:
                    return {**app.run(service.id, **data), "errors": errors}

        class RunTask(Resource):
            decorators = [self.auth.login_required, self.monitor_rest_request]

            def post(self):
                task = db.fetch("task", rbac="schedule", id=request.get_json())
                data = {
                    "trigger": "Scheduler",
                    "creator": task.last_scheduled_by,
                    "runtime": app.get_time(),
                    "task": task.id,
                    **task.initial_payload,
                }
                if task.devices:
                    data["target_devices"] = [device.id for device in task.devices]
                if task.pools:
                    data["target_pools"] = [pool.id for pool in task.pools]
                Thread(target=app.run, args=(task.service.id,), kwargs=data).start()

        class Topology(Resource):
            decorators = [self.auth.login_required, self.monitor_rest_request]

            def post(self, direction):
                if direction == "import":
                    result = app.import_topology(
                        **{
                            "replace": request.form["replace"] == "True",
                            "file": request.files["file"],
                        }
                    )
                    status = 206 if "Partial" in result else 200
                    return result, status
                else:
                    app.export_topology(**request.get_json(force=True))
                    return "Topology Export successfully executed."

        class Search(Resource):
            decorators = [self.auth.login_required, self.monitor_rest_request]

            def post(self):
                rest_body = request.get_json(force=True)
                kwargs = {
                    "draw": 1,
                    "columns": [{"data": column} for column in rest_body["columns"]],
                    "order": [{"column": 0, "dir": "asc"}],
                    "start": 0,
                    "length": rest_body.get("maximum_return_records", 10),
                    "form": rest_body.get("search_criteria", {}),
                    "rest_api_request": True,
                }
                return app.filtering(rest_body["type"], **kwargs)["data"]

        class Sink(Resource):
            def get(self, **_):
                rest_abort(
                    404,
                    message=f"The requested {request.method} endpoint does not exist.",
                )

            post = put = patch = delete = get

        for endpoint in app.rest_endpoints:

            def post(_, ep=endpoint):
                getattr(app, ep)()
                return f"Endpoint {ep} successfully executed."

            api.add_resource(
                type(
                    endpoint,
                    (Resource,),
                    {
                        "decorators": [
                            self.auth.login_required,
                            self.monitor_rest_request,
                        ],
                        "post": post,
                    },
                ),
                f"/rest/{endpoint}",
            )

        api.add_resource(Heartbeat, "/rest/is_alive")
        api.add_resource(RunService, "/rest/run_service")
        api.add_resource(RunTask, "/rest/run_task")
        api.add_resource(Query, "/rest/query/<string:model>")
        api.add_resource(UpdateInstance, "/rest/instance/<string:model>")
        api.add_resource(GetInstance, "/rest/instance/<string:model>/<string:name>")
        api.add_resource(GetConfiguration, "/rest/configuration/<string:name>")
        api.add_resource(Search, "/rest/search")
        api.add_resource(GetResult, "/rest/result/<string:name>/<string:runtime>")
        api.add_resource(Migrate, "/rest/migrate/<string:direction>")
        api.add_resource(Topology, "/rest/topology/<string:direction>")
        api.add_resource(Sink, "/rest/<path:path>")


server = Server()

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
from flask_login import current_user, LoginManager, login_user, logout_user
from flask_restful import abort as rest_abort, Api, Resource
from flask_socketio import join_room, SocketIO
from flask_wtf.csrf import CSRFProtect
from functools import partial, wraps
from itertools import chain
from os import getenv, read, write
from pty import fork
from subprocess import run
from threading import Thread
from time import sleep
from traceback import format_exc

from eNMS import app
from eNMS.database import db
from eNMS.forms import form_classes, form_properties
from eNMS.forms.administration import LoginForm
from eNMS.models import models, property_types, relationships
from eNMS.rest_api import RestApi
from eNMS.setup import properties, themes, visualization


class Server(Flask):
    def __init__(self, mode=None):
        static_folder = str(app.path / "eNMS" / "static")
        super().__init__(__name__, static_folder=static_folder)
        self.rest_api = RestApi()
        self.update_config(mode)
        self.register_extensions()
        self.register_plugins()
        self.configure_login_manager()
        self.configure_context_processor()
        self.configure_errors()
        self.configure_authentication()
        self.configure_routes()
        self.configure_terminal_socket()

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
        self.csrf = CSRFProtect()
        self.csrf.init_app(self)
        self.socketio = SocketIO(self)

    def configure_login_manager(self):
        login_manager = LoginManager()
        login_manager.session_protection = "strong"
        login_manager.init_app(self)

        @login_manager.user_loader
        def user_loader(name):
            return db.get_user(name)

        @login_manager.request_loader
        def request_loader(request):
            return db.get_user(request.form.get("name"))

    def configure_terminal_socket(self):
        def send_data(session, file_descriptor):
            while True:
                self.socketio.sleep(0.1)
                self.socketio.emit(
                    "output",
                    read(file_descriptor, 1024).decode(),
                    namespace="/terminal",
                    room=session,
                )

        @self.socketio.on("input", namespace="/terminal")
        def input(data):
            session = app.ssh_sessions[request.args["session"]]
            write(session["file_descriptor"], data.encode())

        @self.socketio.on("join", namespace="/terminal")
        def on_join(session):
            join_room(session)

        @self.socketio.on("connect", namespace="/terminal")
        def connect():
            session_id = request.args["session"]
            session = app.ssh_sessions.get(session_id)
            if not session:
                return
            device = db.fetch("device", id=session["device"])
            username, password = session["credentials"]
            address, options = getattr(device, session["form"]["address"]), ""
            if app.settings["ssh"]["bypass_key_prompt"]:
                options = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
            process_id, session["file_descriptor"] = fork()
            if process_id:
                task = partial(send_data, session_id, session["file_descriptor"])
                self.socketio.start_background_task(target=task)
            else:
                port = f"-p {device.port}"
                if session["form"]["protocol"] == "telnet":
                    command = f"telnet {address}"
                elif password:
                    ssh_command = f"sshpass -p {password} ssh {options}"
                    command = f"{ssh_command} {username}@{address} {port}"
                else:
                    command = f"ssh {options} {address} {port}"
                run(command.split())

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
        @self.before_request
        def rest_authentication():
            if request.path.startswith("/rest/"):
                user = app.authenticate_user(
                    name=request.authorization["username"],
                    password=request.authorization["password"],
                )
                if not user:
                    return jsonify({"message": "Wrong credentials"}), 401
                else:
                    login_user(user)

    @staticmethod
    def monitor_requests(function):
        @wraps(function)
        def decorated_function(*args, **kwargs):
            remote_address = request.environ["REMOTE_ADDR"]
            client_address = request.environ.get("HTTP_X_FORWARDED_FOR", remote_address)
            if not current_user.is_authenticated:
                app.log(
                    "warning",
                    (
                        f"Unauthorized {request.method} request from "
                        f"'{client_address}' calling the endpoint '{request.url}'"
                    ),
                )
                return redirect(url_for("blueprint.route", page="login"))
            else:
                username = current_user.name
                if request.path.startswith("/rest/"):
                    endpoint = "/".join(request.path.split("/")[:3])
                else:
                    endpoint = f"/{request.path.split('/')[1]}"
                request_property = f"{request.method.lower()}_requests"
                endpoint_rbac = app.rbac[request_property].get(endpoint)
                if not endpoint_rbac:
                    status_code = 404
                elif not current_user.is_admin and (
                    endpoint_rbac == "admin"
                    or endpoint_rbac == "access"
                    and endpoint not in getattr(current_user, request_property)
                ):
                    status_code = 403
                else:
                    try:
                        result = function(*args, **kwargs)
                        status_code = 200
                    except db.rbac_error:
                        status_code = 403
                    except Exception:
                        status_code, traceback = 500, format_exc()
                log = (
                    f"USER: {username} ({client_address}) - "
                    f"{request.method} {endpoint} - ({status_code})"
                )
                if status_code == 500:
                    log += f"\n{traceback}"
                app.log(app.status_log_level[status_code], log, change_log=False)
                if status_code == 200:
                    return result
                elif request.method == "GET" and not endpoint.startswith("/rest/"):
                    return render_template("error.html", error=status_code), status_code
                else:
                    message = {
                        403: "Operation not allowed.",
                        404: "Invalid POST request.",
                        500: "Internal Server Error.",
                    }[status_code]
                    alert = f"Error {status_code} - {message}"
                    return jsonify({"alert": alert}), status_code

        return decorated_function

    def configure_routes(self):
        blueprint = Blueprint("blueprint", __name__, template_folder="../templates")

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
                except Exception as exc:
                    log = f"Authentication error for user '{username}' ({exc})"
                finally:
                    app.log("info" if success else "warning", log, logger="security")
                    if success:
                        return redirect(url_for("blueprint.route", page="dashboard"))
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

        @blueprint.route("/terminal/<session>")
        @self.monitor_requests
        def ssh_connection(session):
            return render_template("terminal.html", session=session)

        @blueprint.route("/<path:_>")
        @self.monitor_requests
        def get_requests_sink(_):
            abort(404)

        @blueprint.route("/rest/<path:page>", methods=["GET", "POST"])
        @self.monitor_requests
        @self.csrf.exempt
        def rest_request(page):
            endpoint, *args = page.split("/")
            if request.method == "POST":
                kwargs = request.get_json(force=True)
            else:
                kwargs = request.args.to_dict()
            with db.session_scope():
                endpoint = self.rest_api.rest_routes[request.method][endpoint]
                return jsonify(getattr(self.rest_api, endpoint)(*args, **kwargs))

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

        class GetResult(Resource):
            decorators = [self.monitor_rest_request]

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

        class Migrate(Resource):
            decorators = [self.monitor_rest_request]

            def post(self, direction):
                kwargs = request.get_json(force=True)
                return getattr(app, f"migration_{direction}")(**kwargs)

        class RunService(Resource):
            decorators = [self.monitor_rest_request]

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
            decorators = [self.monitor_rest_request]

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
            decorators = [self.monitor_rest_request]

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
            decorators = [self.monitor_rest_request]

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
                            self.monitor_rest_request,
                        ],
                        "post": post,
                    },
                ),
                f"/rest/{endpoint}",
            )

        api.add_resource(RunService, "/rest/run_service")
        api.add_resource(RunTask, "/rest/run_task")
        api.add_resource(Search, "/rest/search")
        api.add_resource(GetResult, "/rest/result/<string:name>/<string:runtime>")
        api.add_resource(Migrate, "/rest/migrate/<string:direction>")
        api.add_resource(Topology, "/rest/topology/<string:direction>")


server = Server()

from flask import (
    abort,
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_user, logout_user
from functools import wraps
from logging import info
from os import listdir
from werkzeug.wrappers import Response
import threading

from eNMS import app
from eNMS.database import Session
from eNMS.database.functions import fetch, handle_exception
from eNMS.forms import form_actions, form_classes, form_postprocessing, \
    form_templates
from eNMS.forms.administration import LoginForm
from eNMS.properties.diagram import type_to_diagram_properties
from eNMS.properties.table import table_fixed_columns
from eNMS.handoffssh.ssh_proxy import SshConnection

# from eNMS.handoffssh.client import sshclient


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
        except Exception as e:
            info(f"Authentication failed ({str(e)})")
            abort(403)
    if not current_user.is_authenticated:
        login_form = LoginForm(request.form)
        authentication_methods = [("Local User",) * 2]
        if app.config["ldap"]["active"]:
            authentication_methods.append(("LDAP Domain",) * 2)
        if app.config["tacacs"]["active"]:
            authentication_methods.append(("TACACS",) * 2)
        login_form.authentication_method.choices = authentication_methods
        return render_template("login.html", login_form=login_form)
    return redirect(url_for("blueprint.route", page="dashboard"))


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
            return function(*args, **kwargs)

    return decorated_function


@blueprint.route("/logout")
@monitor_requests
def logout():
    logout_user()
    return redirect(url_for("blueprint.route", page="login"))


@blueprint.route("/administration")
@monitor_requests
def administration():
    return render_template(
        f"pages/administration.html",
        **{
            "endpoint": "administration",
            "folders": listdir(app.path / "files" / "migrations"),
        },
    )


@blueprint.route("/dashboard")
@monitor_requests
def dashboard():
    return render_template(
        f"pages/dashboard.html",
        **{"endpoint": "dashboard", "properties": type_to_diagram_properties},
    )


@blueprint.route("/table/<table_type>")
@monitor_requests
def table(table_type):
    kwargs = {
        "endpoint": f"table/{table_type}",
        "fixed_columns": table_fixed_columns[table_type],
        "type": table_type,
    }
    return render_template(f"pages/table.html", **kwargs)


@blueprint.route("/view/<view_type>")
@monitor_requests
def view(view_type):
    return render_template(
        f"pages/view.html", **{"endpoint": "view", "view_type": view_type}
    )


@blueprint.route("/workflow_builder")
@monitor_requests
def workflow_builder():
    workflow, workflow_path = None, session.get("path", None)
    if workflow_path:
        workflow = fetch("workflow",
                         allow_none=True,
                         id=workflow_path.split(">")[-1])
    return render_template(
        f"pages/workflow_builder.html",
        **{
            "endpoint": "workflow_builder",
            "workflow": workflow.serialized if workflow else None,
            "path": session.get("path", ""),
        },
    )


@blueprint.route("/form/<form_type>")
@monitor_requests
def form(form_type):
    kwargs = (
        {"fixed_columns": table_fixed_columns[form_type], "type": form_type}
        if form_type == "result"
        else {}
    )
    return render_template(
        f"forms/{form_templates.get(form_type, 'base')}_form.html",
        **{
            "endpoint": f"form/{form_type}",
            "action": form_actions.get(form_type),
            "form": form_classes[form_type](request.form),
            "form_type": form_type,
            **kwargs,
        },
    )


@blueprint.route("/handoffssh/<id>", methods=["POST"])
@monitor_requests
def gensshhandoff(id):
    calling_data = request.values
    # device = fetch("device", id=calling_data['id'])
    device = fetch("device", id=id)

    # Setup and start server for user
    if calling_data["credentials"] == "device":
        userserver = SshConnection(
            device.ip_address,
            device.port,
            device.username,
            device.password,
            current_user.name,
        )
    elif calling_data["credentials"] == "user":
        userserver = SshConnection(
            device.ip_address, device.port, None, None, current_user.name,
        )

    ts = threading.Thread(
        target=userserver.start,
        args=(device, calling_data["credentials"]),
        name="ServerThread",
    )
    ts.start()

    return {
        "listeningport": userserver.listeningport,
        "username": current_user.name,
        "calling_password": userserver.calling_password,
        "device": device.name,
        "device_ip": device.ip_address,
    }


@blueprint.route("/view_service_results/<int:id>")
@monitor_requests
def view_service_results(id):
    result = fetch("run", id=id).result().result
    return f"<pre>{app.str_dict(result)}</pre>"


@blueprint.route("/download_output/<id>")
@monitor_requests
def download_output(id):
    data = fetch("data", id=id)
    filename = f"{data.device_name}-\
                {data.command}-\
                {app.strip_all(data.runtime)}"
    return Response(
        (f"{line}\n" for line in data.output.splitlines()),
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment;filename={filename}.txt"},
    )


@blueprint.route("/<path:_>")
@monitor_requests
def get_requests_sink(_):
    abort(404)


@blueprint.route("/", methods=["POST"])
@blueprint.route("/<path:page>", methods=["POST"])
@monitor_requests
def route(page):
    f, *args = page.split("/")
    if f not in app.json_endpoints + app.form_endpoints:
        return jsonify({"alert": "Invalid POST request."})
    form_type = request.form.get("form_type")
    if f in app.json_endpoints:
        result = getattr(app, f)(*args, **request.json)
    elif form_type:
        form = form_classes[form_type](request.form)
        if not form.validate_on_submit():
            return jsonify({"invalid_form": True, **{"errors": form.errors}})
        result = getattr(app, f)(*args,
                                 **form_postprocessing(form, request.form))
    else:
        result = getattr(app, f)(*args)
    try:
        Session.commit()
        return jsonify(result)
    except Exception as exc:
        raise exc
        Session.rollback()
        if app.config["app"]["config_mode"] == "debug":
            raise
        return jsonify({"alert": handle_exception(str(exc))})

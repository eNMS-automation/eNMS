from flask import (
    abort,
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from functools import wraps
from logging import info
from os import listdir
from typing import Any, Callable
from werkzeug.wrappers import Response

from eNMS.controller import controller
from eNMS.database import Session
from eNMS.database.functions import fetch, handle_exception
from eNMS.forms import form_actions, form_classes, form_postprocessing, form_templates
from eNMS.forms.administration import LoginForm
from eNMS.forms.automation import ServiceTableForm
from eNMS.models import models
from eNMS.properties.diagram import type_to_diagram_properties
from eNMS.properties.table import (
    filtering_properties,
    table_fixed_columns,
    table_properties,
)


blueprint = Blueprint("blueprint", __name__, template_folder="templates")


def monitor_requests(function: Callable) -> Callable:
    @wraps(function)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if not current_user.is_authenticated:
            controller.log(
                "warning",
                (
                    f"Unauthorized {request.method} request from "
                    f"'{request.remote_addr}' calling the endpoint '{request.url}'"
                ),
            )
            abort(403)
        else:
            return function(*args, **kwargs)

    return decorated_function


@blueprint.route("/")
def site_root() -> Response:
    return redirect(url_for("blueprint.route", page="login"))


@blueprint.route("/<path:_>")
@monitor_requests
def get_requests_sink(_: str) -> Response:
    abort(404)


@blueprint.route("/login", methods=["GET", "POST"])
def login() -> Any:
    if request.method == "POST":
        try:
            user = controller.authenticate_user(**request.form.to_dict())
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
        if controller.use_ldap:
            authentication_methods.append(("LDAP Domain",) * 2)
        if controller.use_tacacs:
            authentication_methods.append(("TACACS",) * 2)
        login_form.authentication_method.choices = authentication_methods
        return render_template("login.html", login_form=login_form)
    return redirect(url_for("blueprint.route", page="dashboard"))


@blueprint.route("/logout")
@monitor_requests
def logout() -> Response:
    logout_user()
    return redirect(url_for("blueprint.route", page="login"))


@blueprint.route("/administration")
@monitor_requests
def administration() -> str:
    return render_template(
        f"pages/administration.html",
        **{
            "endpoint": "administration",
            "folders": listdir(current_app.path / "projects" / "migrations"),
        },
    )


@blueprint.route("/dashboard")
@monitor_requests
def dashboard() -> str:
    return render_template(
        f"pages/dashboard.html",
        **{"endpoint": "dashboard", "properties": type_to_diagram_properties},
    )


@blueprint.route("/table/<table_type>")
@monitor_requests
def table(table_type: str) -> str:
    kwargs = {
        "endpoint": f"table/{table_type}",
        "properties": table_properties[table_type],
        "filtering_properties": filtering_properties[table_type],
        "fixed_columns": table_fixed_columns[table_type],
        "type": table_type,
    }
    if table_type == "service":
        service_table_form = ServiceTableForm(request.form)
        service_table_form.services.choices = sorted(
            (service, service)
            for service in models
            if service != "Service" and service.endswith("Service")
        )
        kwargs["service_table_form"] = service_table_form
    return render_template(f"pages/table.html", **kwargs)


@blueprint.route("/view/<view_type>")
@monitor_requests
def view(view_type: str) -> str:
    return render_template(
        f"pages/view.html", **{"endpoint": "view", "view_type": view_type}
    )


@blueprint.route("/workflow_builder")
@monitor_requests
def workflow_builder() -> str:
    workflow = fetch("Workflow", allow_none=True, id=session.get("workflow", None))
    service_table_form = ServiceTableForm(request.form)
    service_table_form.services.choices = sorted(
        (service, service)
        for service in models
        if service != "Service" and service.endswith("Service")
    )
    return render_template(
        f"pages/workflow_builder.html",
        service_table_form=service_table_form,
        **{
            "endpoint": "workflow_builder",
            "workflow": workflow.serialized if workflow else None,
        },
    )


@blueprint.route("/calendar/<calendar_type>")
@monitor_requests
def calendar(calendar_type: str) -> str:
    return render_template(
        f"pages/calendar.html",
        **{"calendar_type": calendar_type, "endpoint": "calendar"},
    )


@blueprint.route("/form/<form_type>")
@monitor_requests
def form(form_type: str) -> str:
    return render_template(
        f"forms/{form_templates.get(form_type, 'base')}_form.html",
        **{
            "endpoint": f"form/{form_type}",
            "action": form_actions.get(form_type),
            "form": form_classes[form_type](request.form),
            "form_type": form_type,
        },
    )


@blueprint.route("/view_job_results/<int:job_id>/<runtime>")
@login_required
def view_job_results(job_id: int, runtime: str) -> str:
    runtime = runtime.replace("$", " ")
    result = fetch("Result", job_id=job_id, runtime=runtime).result
    return f"<pre>{controller.str_dict(result)}</pre>"


@blueprint.route("/download_configuration/<name>")
@login_required
def download_configuration(name: str) -> Response:
    try:
        return send_file(
            filename_or_fp=str(
                current_app.path / "git" / "configurations" / name / name
            ),
            as_attachment=True,
            attachment_filename=f"configuration_{name}.txt",
        )
    except FileNotFoundError:
        return jsonify("No configuration stored")


@blueprint.route("/", methods=["POST"])
@blueprint.route("/<path:page>", methods=["POST"])
@monitor_requests
def route(page: str) -> Response:
    f, *args = page.split("/")
    if f not in controller.valid_post_endpoints:
        return jsonify({"error": "Invalid POST request."})
    form_type = request.form.get("form_type")
    if form_type:
        form = form_classes[form_type](request.form)
        if not form.validate_on_submit():
            return jsonify({"invalid_form": True, **{"errors": form.errors}})
        result = getattr(controller, f)(*args, **form_postprocessing(request.form))
    elif f == "filtering":
        result = getattr(controller, f)(*args, request.form)
    else:
        result = getattr(controller, f)(*args)
    try:
        Session.commit()
        return jsonify(result)
    except Exception as exc:
        Session.rollback()
        if controller.enms_config_mode == "Debug":
            raise
        return jsonify({"error": handle_exception(str(exc))})

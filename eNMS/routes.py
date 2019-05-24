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
from sqlalchemy import and_
from typing import Any, Callable
from werkzeug.wrappers import Response

from eNMS.controller import controller
from eNMS.database import Session
from eNMS.database.functions import fetch
from eNMS.forms import form_actions, form_classes, form_postprocessing, form_templates
from eNMS.forms.administration import LoginForm
from eNMS.forms.automation import ServiceTableForm
from eNMS.extensions import cache
from eNMS.models import models
from eNMS.properties.diagram import type_to_diagram_properties
from eNMS.properties.objects import link_colors
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
def login() -> Response:
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
@cache.cached(timeout=0)
@monitor_requests
def administration() -> dict:
    return render_template(
        f"pages/administration.html",
        **{
            "endpoint": "administration",
            "folders": listdir(current_app.path / "projects" / "migrations"),
        },
    )


@blueprint.route("/dashboard")
@cache.cached(timeout=0)
@monitor_requests
def dashboard() -> dict:
    return render_template(
        f"pages/dashboard.html",
        **{"endpoint": "dashboard", "properties": type_to_diagram_properties},
    )


@blueprint.route("/table/<table_type>")
@monitor_requests
def table(table_type: str) -> dict:
    kwargs = {
        "endpoint": f"table/{table_type}",
        "properties": table_properties[table_type],
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
def view(view_type: str) -> dict:
    return render_template(
        f"pages/view.html",
        **{"endpoint": "view", "link_colors": link_colors, "view_type": view_type},
    )


@blueprint.route("/workflow_builder")
@monitor_requests
def workflow_builder() -> dict:
    workflow = fetch("Workflow", id=session.get("workflow", None))
    return render_template(
        f"pages/workflow_builder.html",
        **{
            "endpoint": "workflow_builder",
            "workflow": workflow.serialized if workflow else None,
        },
    )


@blueprint.route("/calendar")
@cache.cached(timeout=0)
@monitor_requests
def calendar() -> dict:
    return render_template(f"pages/calendar.html", **{"endpoint": "calendar"})


@blueprint.route("/form/<form_type>")
@cache.cached(timeout=0)
@monitor_requests
def form(form_type: str) -> dict:
    return render_template(
        f"forms/{form_templates.get(form_type, 'base')}_form.html",
        **{
            "endpoint": f"form/{form_type}",
            "action": form_actions.get(form_type),
            "form": form_classes[form_type](request.form),
            "form_type": form_type,
        },
    )


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


@blueprint.route("/filtering/<table>")
@monitor_requests
def filtering(table: str) -> dict:
    model = models.get(table, models["Device"])
    properties = table_properties[table]
    try:
        order_property = properties[int(request.args["order[0][column]"])]
    except IndexError:
        order_property = "name"
    order = getattr(getattr(model, order_property), request.args["order[0][dir]"])()
    constraints = []
    for property in filtering_properties[table]:
        value = request.args.get(f"form[{property}]")
        if value:
            constraints.append(getattr(model, property).contains(value))
    result = Session.query(model).filter(and_(*constraints)).order_by(order)
    if table in ("device", "link", "configuration"):
        pools = [int(id) for id in request.args.getlist("form[pools][]")]
        if pools:
            result = result.filter(model.pools.any(models["pool"].id.in_(pools)))
    return jsonify(
        {
            "draw": int(request.args["draw"]),
            "recordsTotal": len(Session.query(model).all()),
            "recordsFiltered": len(result.all()),
            "data": [
                [getattr(obj, property) for property in properties]
                + obj.generate_row(table)
                for obj in result.limit(int(request.args["length"]))
                .offset(int(request.args["start"]))
                .all()
            ],
        }
    )


@blueprint.route("/", methods=["POST"])
@blueprint.route("/<path:page>", methods=["POST"])
@monitor_requests
def route(page: str) -> Response:
    f, *args = page.split("/")
    kwargs: dict = {}
    if f not in controller.valid_post_endpoints:
        return jsonify({"error": "Invalid POST request."})
    form_type = request.form.get("form_type")
    if form_type:
        form = form_classes[form_type](request.form)
        if not form.validate_on_submit():
            return jsonify({"invalid_form": True, **{"errors": form.errors}})
        kwargs = form_postprocessing(request.form)
    try:
        result = getattr(controller, f)(*args, **kwargs)
        Session.commit()
        return jsonify(result)
    except Exception as e:
        if controller.enms_config_mode == "Develop":
            raise
        return jsonify({"error": str(e)})

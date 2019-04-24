from collections import Counter
from datetime import datetime
from difflib import SequenceMatcher
from flask import (
    abort,
    current_app as app,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask_login import current_user, login_user, logout_user
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from json import dumps, loads
from json.decoder import JSONDecodeError
from ldap3 import Connection, NTLM, SUBTREE
from logging import info
from flask.wrappers import Response
from ipaddress import IPv4Network
from os import listdir
from pynetbox import api as netbox_api
from re import search, sub
from requests import get as http_get
from requests.exceptions import ConnectionError
from simplekml import Kml
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError, DataError
from subprocess import Popen
from typing import Any, Dict, List, Union

from eNMS.controller import controller
from eNMS.modules import (
    bp,
    db,
    ldap_client,
    scheduler,
    tacacs_client,
    USE_LDAP,
    USE_TACACS,
)
from eNMS.forms import (
    form_classes,
    form_templates,
    AdministrationForm,
    DatabaseHelpersForm,
    LoginForm,
    MigrationsForm,
    CompareResultsForm,
    GoogleEarthForm,
    ImportExportForm,
    LibreNmsForm,
    NetboxForm,
    OpenNmsForm,
    WorkflowBuilderForm,
)
from eNMS.framework import (
    delete,
    delete_all,
    factory,
    fetch,
    fetch_all,
    fetch_all_visible,
    get,
    get_one,
    objectify,
    post,
    permission_required,
)
from eNMS.helpers import migrate_export, migrate_import, scheduler_job, str_dict
from eNMS.models import classes, service_classes
from eNMS.modules import bp
from eNMS.properties import (
    cls_to_properties,
    default_diagrams_properties,
    google_earth_styles,
    link_subtype_to_color,
    pretty_names,
    private_properties,
    property_types,
    reverse_pretty_names,
    subtype_sizes,
    table_fixed_columns,
    table_properties,
    type_to_diagram_properties,
)


@bp.route("/<endpoint>", methods=["GET"])
@login_required
def get_route(endpoint: str) -> Response:
    ctx = getattr(controller, endpoint)() or {}
    if not isinstance(ctx, dict):
        return ctx
    ctx["endpoint"] = endpoint
    info(
        f"User '{current_user.name}' ({request.remote_addr})"
        f"calling the endpoint {endpoint} (GET)"
    )
    return render_template(f"{ctx.pop('template', 'pages/' + endpoint)}.html", **ctx)


@bp.route("/<endpoint>", methods=["POST"])
@login_required
def post_route(endpoint: str) -> Response:
    data = {**request.form.to_dict(), **{"creator": current_user.id}}
    for property in data.get("list_fields", "").split(","):
        data[property] = request.form.getlist(property)
    for property in data.get("boolean_fields", "").split(","):
        data[property] = property in request.form
    request.form = data
    func, *args = endpoint.split("@")
    info(
        f"User '{current_user.name}' ({request.remote_addr})"
        f" calling the endpoint {request.url} (POST)"
    )
    try:
        result = getattr(controller, func)(*args)
        db.session.commit()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})


@bp.route("/filtering/<table>", methods=["GET"])
@login_required
def filtering(table: str) -> Response:
    return jsonify(controller.filtering(table, request.args))


@get("/logout")
def logout() -> Response:
    logout_user()
    return redirect(url_for("admin_blueprint.login"))


@get("/<form_type>_form", "View")
def route_form(form_type: str) -> dict:
    return dict(
        form=form_classes.get(form_type, FlaskForm)(request.form),
        form_type=form_type,
        template=f"forms/{form_templates.get(form_type, form_type + '_form')}",
    )


@get("/<table_type>_management", "View")
def route_table(table_type: str) -> dict:
    return dict(
        properties=table_properties[table_type],
        fixed_columns=table_fixed_columns[table_type],
        type=table_type,
        template="pages/table",
    )


@post("/scheduler/<action>", "Admin")
def scheduler_action(action: str) -> bool:
    getattr(scheduler, action)()


@bp.route("/")
def site_root() -> Response:
    return redirect(url_for("bp.login"))

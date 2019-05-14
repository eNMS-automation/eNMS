from flask import (
    abort,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask_login import current_user
from flask_wtf import FlaskForm
from flask.wrappers import Response
from json.decoder import JSONDecodeError
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from typing import List
from werkzeug.wrappers.response import Response

from eNMS.controller import controller
from eNMS.database import Session
from eNMS.database.functions import delete, factory, fetch, fetch_all, Session
from eNMS.dispatcher import dispatcher
from eNMS.forms import form_actions, form_classes, form_postprocessing, form_templates
from eNMS.forms.administration import LoginForm
from eNMS.forms.automation import ServiceTableForm
from eNMS.extensions import bp, cache
from eNMS.models import models
from eNMS.properties.diagram import type_to_diagram_properties
from eNMS.properties.table import (
    filtering_properties,
    table_fixed_columns,
    table_properties,
)


@bp.route("/")
def site_root() -> Response:
    return redirect(url_for("bp.route", page="login"))


@bp.route("/<page>", methods=["GET", "POST"])
@cache.cached(timeout=0, unless=controller.unless_cache)
def route(page: str) -> Response:
    if not current_user.is_authenticated:
        controller.log(
            "warning",
            (
                f"Unauthenticated {request.method} request from "
                f"'{request.remote_addr}' calling the endpoint '{request.url}'"
            ),
        )
        if request.method == "POST":
            return dispatcher.login() if page == "login" else False
        if request.method == "GET" and page != "login":
            return current_app.login_manager.unauthorized()
    func, *args = page.split("-")

    if request.method == "POST":
        form_type = request.form.get("form_type")
        if form_type:
            form = form_classes[form_type](request.form)
            if not form.validate_on_submit():
                return jsonify({"invalid_form": True, **{"errors": form.errors}})
            request.form = form_postprocessing(request.form)
    # try:
    # if not hasattr(dispatcher, func):
    #    abort(404)
    result = getattr(dispatcher if request.method == "GET" else controller, func)(*args)
    Session.commit()
    # except Exception as e:
    # result = {"error": str(e)}
    if isinstance(result, Response) or isinstance(result, str):
        return result
    elif request.method == "POST" or func == "filtering":
        return jsonify(result)
    else:
        return render_template(
            f"{result.pop('template', 'pages/' + page)}.html",
            **{"endpoint": page, **result},
        )

from flask import (
    abort,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user
from logging import info, warning
from werkzeug.wrappers.response import Response

from eNMS.dispatcher import dispatcher
from eNMS.forms import form_classes, form_postprocessing
from eNMS.extensions import bp


@bp.route("/")
def site_root() -> Response:
    return redirect(url_for("bp.route", page="login"))


@bp.route("/<page>", methods=["GET", "POST"])
@cache.cached(timeout=10000)
def route(page: str) -> Response:
    print(request.form)
    if not current_user.is_authenticated:
        warning(
            f"Unauthenticated {request.method} request from "
            f"{request.remote_addr} calling the endpoint {request.url}"
        )
        if request.method == "POST":
            return dispatcher.login() if page == "login" else False
        if request.method == "GET" and page != "login":
            return current_app.login_manager.unauthorized()
    else:
        info(
            f"User '{current_user.name}' {request.remote_addr} "
            f"on the endpoint '{request.url}' ({request.method})"
        )
    func, *args = page.split("-")
    if not hasattr(dispatcher, func):
        abort(404)
    if request.method == "POST":
        form_type = request.form.get("form_type")
        if form_type:
            form = form_classes[form_type](request.form)
            if not form.validate_on_submit():
                return jsonify({"invalid_form": True, **{"errors": form.errors}})
            request.form = form_postprocessing(request.form)
    try:
        result = getattr(dispatcher, func)(*args)
    except Exception as e:
        result = {"error": str(e)}
    if isinstance(result, Response) or isinstance(result, str):
        return result
    elif request.method == "POST" or func == "filtering":
        return jsonify(result)
    else:
        return render_template(
            f"{result.pop('template', 'pages/' + page)}.html",
            **{"endpoint": page, **result},
        )

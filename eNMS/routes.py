from flask import current_app, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from logging import info
from werkzeug.wrappers.response import Response

from eNMS.dispatcher import dispatcher
from eNMS.forms import form_postprocessing
from eNMS.modules import bp, db


@bp.route("/")
def site_root() -> Response:
    return redirect(url_for("bp.get_route", page="login"))


@bp.route("/<page>")
def get_route(page: str) -> Response:
    if not current_user.is_authenticated and page != "login":
        return current_app.login_manager.unauthorized()
    func, *args = page.split("-")
    ctx = getattr(dispatcher, func)(*args) or {}
    if not isinstance(ctx, dict):
        return ctx
    ctx["endpoint"] = page
    info(
        f"User '{current_user.name}' ({request.remote_addr})"
        f"calling the endpoint {page} (GET)"
    )
    if func == "filtering":
        return jsonify(ctx)
    return render_template(f"{ctx.pop('template', 'pages/' + page)}.html", **ctx)


@bp.route("/<page>", methods=["POST"])
@login_required
def post_route(page: str) -> Response:
    if "form_type" in request.form:
        request.form = form_postprocessing(request.form)
    func, *args = page.split("-")
    info(
        f"User '{current_user.name}' ({request.remote_addr})"
        f" calling the endpoint {request.url} (POST)"
    )
    # try:
    result = getattr(dispatcher, func)(*args)
    db.session.commit()
    return result if type(result) == Response else jsonify(result)
    # except Exception as e:
    #     return jsonify({"error": str(e)})

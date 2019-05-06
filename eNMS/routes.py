from flask import current_app, jsonify, redirect, render_template, request, url_for
from flask_login import current_user
from logging import info, warning
from werkzeug.wrappers.response import Response

from eNMS.dispatcher import dispatcher
from eNMS.forms import form_classes, form_postprocessing
from eNMS.modules import bp


@bp.route("/")
def site_root() -> Response:
    return redirect(url_for("bp.get_route", page="login"))


@bp.route("/<page>")
def get_route(page: str) -> Response:
    if not current_user.is_authenticated and page != "login":
        warning(
            f"Unauthenticated GET request from {request.remote_addr} "
            f" calling the endpoint {request.url}"
        )
        return current_app.login_manager.unauthorized()
    func, *args = page.split("-")
    ctx = getattr(dispatcher, func)(*args) or {}
    if not isinstance(ctx, dict):
        return ctx
    ctx["endpoint"] = page
    info(
        f"User '{current_user.name}' from {request.remote_addr} "
        f"calling the endpoint {page} (GET)"
    )
    if func == "filtering":
        return jsonify(ctx)
    return render_template(f"{ctx.pop('template', 'pages/' + page)}.html", **ctx)


@bp.route("/<page>", methods=["POST"])
def post_route(page: str) -> Response:
    if not current_user.is_authenticated:
        if page == "login":
            return dispatcher.login()
        else:
            warning(
                f"Unauthenticated POST request ({request.remote_addr})"
                f"calling the endpoint {request.url}"
            )
            return False
    info(
        f"User '{current_user.name}' {request.remote_addr} "
        f"calling the endpoint {request.url} (POST)"
    )
    form_type = request.form.get("form_type")
    if form_type:
        form = form_classes[form_type](request.form)
        if not form.validate_on_submit():
            return jsonify({"invalid_form": True, **{"errors": form.errors}})
        request.form = form_postprocessing(request.form)
    func, *args = page.split("-")
    # try:
    result = getattr(dispatcher, func)(*args)
    db.session.commit()
    return result if type(result) == Response else jsonify(result)
    # except Exception as e:
    #     return jsonify({"error": str(e)})

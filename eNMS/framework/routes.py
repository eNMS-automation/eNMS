from flask import (
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_user, logout_user

from eNMS import app
from eNMS.database import Session
from eNMS.database.functions import fetch, handle_exception
from eNMS.forms import form_actions, form_classes, form_postprocessing, form_templates
from eNMS.framework import web_app
from eNMS.setup import properties


@blueprint.route("/logout")
@monitor_requests
def logout():
    logout_user()
    return redirect(url_for("blueprint.route", page="login"))


@blueprint.route("/table/<table_type>")
@monitor_requests
def table(table_type):
    return render_template(
        f"table.html", **{"endpoint": f"table/{table_type}", "type": table_type}
    )


@blueprint.route("/view/<view_type>")
@monitor_requests
def view(view_type):
    return render_template(
        f"visualization.html", **{"endpoint": "view", "view_type": view_type}
    )


@blueprint.route("/workflow_builder")
@monitor_requests
def workflow_builder():
    return render_template(f"workflow.html", endpoint="workflow_builder")


@blueprint.route("/form/<form_type>")
@monitor_requests
def form(form_type):
    return render_template(
        f"forms/{form_templates.get(form_type, 'base')}.html",
        **{
            "endpoint": f"forms/{form_type}",
            "action": form_actions.get(form_type),
            "form": form_classes[form_type](request.form),
            "form_type": form_type,
        },
    )


@blueprint.route("/help/<path:path>")
@monitor_requests
def help(path):
    return render_template(f"help/{path}.html")


@blueprint.route("/view_service_results/<int:id>")
@monitor_requests
def view_service_results(id):
    result = fetch("run", id=id).result().result
    return f"<pre>{app.str_dict(result)}</pre>"


@blueprint.route("/download_file/<path:path>")
@monitor_requests
def download_file(path):
    return send_file(f"/{path}", as_attachment=True)


@blueprint.route("/<path:_>")
@monitor_requests
def get_requests_sink(_):
    abort(404)




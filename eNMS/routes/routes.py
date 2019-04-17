from collections import Counter
from flask_wtf import FlaskForm
from json.decoder import JSONDecodeError
from logging import info
from flask import jsonify, redirect, request, url_for
from flask_login import current_user
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from typing import List
from werkzeug.wrappers import Response

from eNMS import db
from eNMS.classes import classes
from eNMS.extensions import bp
from eNMS.forms import form_classes, form_templates
from eNMS.functions import (
    delete,
    factory,
    fetch,
    fetch_all,
    fetch_all_visible,
    get,
    post,
)
from eNMS.properties import (
    default_diagrams_properties,
    reverse_pretty_names,
    table_fixed_columns,
    table_properties,
    type_to_diagram_properties,
)


@bp.route("/")
def site_root() -> Response:
    return redirect(url_for("bp.login"))


@get("/dashboard")
def dashboard() -> dict:
    on_going = {
        "Running services": len(
            [service for service in fetch_all("Service") if service.status == "Running"]
        ),
        "Running workflows": len(
            [
                workflow
                for workflow in fetch_all("Workflow")
                if workflow.status == "Running"
            ]
        ),
        "Scheduled tasks": len(
            [task for task in fetch_all("Task") if task.status == "Active"]
        ),
    }
    return dict(
        properties=type_to_diagram_properties,
        default_properties=default_diagrams_properties,
        counters={**{cls: len(fetch_all_visible(cls)) for cls in classes}, **on_going},
    )


@get(bp, "/import_export", "View")
def import_export() -> dict:
    return dict(
        import_export_form=ImportExportForm(request.form),
        librenms_form=LibreNmsForm(request.form),
        netbox_form=NetboxForm(request.form),
        opennms_form=OpenNmsForm(request.form),
        google_earth_form=GoogleEarthForm(request.form),
        parameters=get_one("Parameters"),
    )


@get(bp, "/download_configuration/<name>", "View")
def download_configuration(name: str) -> Response:
    try:
        return send_file(
            filename_or_fp=str(app.path / "git" / "configurations" / name / name),
            as_attachment=True,
            attachment_filename=f"configuration_{name}.txt",
        )
    except FileNotFoundError:
        return jsonify("No configuration stored")


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


@get("/filtering/<table>")
def filtering(table: str) -> Response:
    model = classes.get(table, classes["Device"])
    properties = table_properties[table]
    if table in ("configuration", "device"):
        properties.append("current_configuration")
    try:
        order_property = properties[int(request.args["order[0][column]"])]
    except IndexError:
        order_property = "name"
    order = getattr(getattr(model, order_property), request.args["order[0][dir]"])()
    constraints = []
    for property in properties:
        value = request.args.get(f"form[{property}]")
        if value:
            constraints.append(getattr(model, property).contains(value))
    result = db.session.query(model).filter(and_(*constraints)).order_by(order)
    if table in ("device", "link", "configuration"):
        pools = [int(id) for id in request.args.getlist("form[pools][]")]
        if pools:
            result = result.filter(model.pools.any(classes["pool"].id.in_(pools)))
    return jsonify(
        {
            "draw": int(request.args["draw"]),
            "recordsTotal": len(model.query.all()),
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


@post("/get/<cls>/<id>", "View")
def get_instance(cls: str, id: str) -> dict:
    instance = fetch(cls, id=id)
    info(f"{current_user.name}: GET {cls} {instance.name} ({id})")
    return instance.serialized


@post("/get_all/<cls>", "View")
def get_all_instances(cls: str) -> List[dict]:
    info(f"{current_user.name}: GET ALL {cls}")
    return [instance.get_properties() for instance in fetch_all_visible(cls)]


@post("/update/<cls>", "Edit")
def update_instance(cls: str) -> dict:
    try:
        instance = factory(cls, **request.form)
        info(f"{current_user.name}: UPDATE {cls} " f"{instance.name} ({instance.id})")
        return instance.serialized
    except JSONDecodeError:
        return {"error": "Invalid JSON syntax (JSON field)"}
    except IntegrityError:
        return {"error": "An object with the same name already exists"}


@post("/delete/<cls>/<id>", "Edit")
def delete_instance(cls: str, id: str) -> dict:
    instance = delete(cls, id=id)
    info(f'{current_user.name}: DELETE {cls} {instance["name"]} ({id})')
    return instance


@post("/counters/<property>/<type>")
def get_counters(property: str, type: str) -> Counter:
    objects = fetch_all(type)
    if property in reverse_pretty_names:
        property = reverse_pretty_names[property]
    return Counter(map(lambda o: str(getattr(o, property)), objects))


@post("/shutdown", "Admin")
def shutdown() -> str:
    info(f"{current_user.name}: SHUTDOWN eNMS")
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        raise RuntimeError("Not running with the Werkzeug Server")
    func()
    return "Server shutting down..."

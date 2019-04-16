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
from eNMS.base import bp
from eNMS.classes import classes
from eNMS.forms import form_classes, form_templates
from eNMS.functions import delete, factory, fetch, fetch_all_visible, get, post
from eNMS.properties import table_fixed_columns, table_properties


@bp.route("/")
def site_root() -> Response:
    return redirect(url_for("admin_blueprint.login"))


@get(bp, "/<form_type>_form", "View")
def route_form(form_type: str) -> dict:
    return dict(
        form=form_classes.get(form_type, FlaskForm)(request.form),
        form_type=form_type,
        template=f"forms/{form_templates.get(form_type, form_type + '_form')}",
    )


@get(bp, "/<_>/<table_type>_management", "View")
def route_table(_: str, table_type: str) -> dict:
    return dict(
        properties=table_properties[table_type],
        fixed_columns=table_fixed_columns[table_type],
        type=table_type,
        template="table",
    )


@get(bp, "/server_side_processing/<table>")
def server_side_processing(table: str) -> Response:
    print(request.args)
    model, properties = classes.get(table, classes["Device"]), table_properties[table]
    try:
        order_property = properties[int(request.args["order[0][column]"])]
    except IndexError:
        order_property = "name"
    order_direction = request.args["order[0][dir]"]
    constraints = []
    for property in properties:
        value = request.args.get(f"form[{property}]")
        if not value:
            continue
        else:
            constraints.append(getattr(model, property).contains(value))
    order = getattr(getattr(model, order_property), order_direction)()
    result = db.session.query(model).filter(and_(*constraints)).order_by(order)
    if table == "configuration":
        search_text = request.args.get("form[{configuration}]")
        if search_text:
            result = result.filter(model.current_configuration.contains(search_text))
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


@post(bp, "/get/<cls>/<id>", "View")
def get_instance(cls: str, id: str) -> dict:
    instance = fetch(cls, id=id)
    info(f"{current_user.name}: GET {cls} {instance.name} ({id})")
    return instance.serialized


@post(bp, "/get_all/<cls>", "View")
def get_all_instances(cls: str) -> List[dict]:
    info(f"{current_user.name}: GET ALL {cls}")
    return [instance.get_properties() for instance in fetch_all_visible(cls)]


@post(bp, "/update/<cls>", "Edit")
def update_instance(cls: str) -> dict:
    try:
        instance = factory(cls, **request.form)
        info(f"{current_user.name}: UPDATE {cls} " f"{instance.name} ({instance.id})")
        return instance.serialized
    except JSONDecodeError:
        return {"error": "Invalid JSON syntax (JSON field)"}
    except IntegrityError:
        return {"error": "An object with the same name already exists"}


@post(bp, "/delete/<cls>/<id>", "Edit")
def delete_instance(cls: str, id: str) -> dict:
    instance = delete(cls, id=id)
    info(f'{current_user.name}: DELETE {cls} {instance["name"]} ({id})')
    return instance


@post(bp, "/shutdown", "Admin")
def shutdown() -> str:
    info(f"{current_user.name}: SHUTDOWN eNMS")
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        raise RuntimeError("Not running with the Werkzeug Server")
    func()
    return "Server shutting down..."

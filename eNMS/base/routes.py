from collections import Counter
from json.decoder import JSONDecodeError
from logging import info
from flask import jsonify, redirect, request, url_for
from flask_login import current_user
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.attributes import InstrumentedAttribute
from typing import List
from werkzeug.wrappers import Response

from eNMS import db
from eNMS.base import bp
from eNMS.classes import classes
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
    table_properties,
    reverse_pretty_names,
    type_to_diagram_properties,
)


@bp.route("/")
def site_root() -> Response:
    return redirect(url_for("admin_blueprint.login"))


@get(bp, "/server_side_processing/<cls>/<table>")
def server_side_processing(cls: str, table: str) -> Response:
    model, properties = classes[cls], table_properties[table]
    try:
        order_property = properties[int(request.args["order[0][column]"])]
    except IndexError:
        order_property = "name"
    order_direction = request.args["order[0][dir]"]
    filtered = (
        db.session.query(model)
        .filter(
            and_(
                *[
                    getattr(model, property).contains(value)
                    if isinstance(getattr(model, property), InstrumentedAttribute)
                    else getattr(model, property) == value
                    for property, value in {
                        property: request.args[f"columns[{i}][search][value]"]
                        for i, property in enumerate(properties)
                        if request.args[f"columns[{i}][search][value]"]
                    }.items()
                ]
            )
        )
        .order_by(getattr(getattr(model, order_property), order_direction)())
    )
    if table == "configuration":
        search_text = request.args["columns[6][search][value]"]
        if search_text:
            filtered = filtered.filter(
                model.current_configuration.contains(search_text)
            )
    if table in ("device", "link", "configuration"):
        filtered = filtered.filter(
            model.pools.any(
                classes["pool"].id.in_(
                    [
                        int(pool_id)
                        for pool_id in request.args.getlist("pools[]")
                        if pool_id
                    ]
                )
            )
        )
    return jsonify(
        {
            "draw": int(request.args["draw"]),
            "recordsTotal": len(model.query.all()),
            "recordsFiltered": len(filtered.all()),
            "data": [
                [getattr(obj, property) for property in properties]
                + obj.generate_row(table)
                for obj in filtered.limit(int(request.args["length"]))
                .offset(int(request.args["start"]))
                .all()
            ],
        }
    )


@get(bp, "/dashboard")
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


@post(bp, "/counters/<property>/<type>")
def get_counters(property: str, type: str) -> Counter:
    objects = fetch_all(type)
    if property in reverse_pretty_names:
        property = reverse_pretty_names[property]
    return Counter(map(lambda o: str(getattr(o, property)), objects))


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

from flask import request
from sqlalchemy import and_
from typing import Union

from eNMS import db
from eNMS.classes import classes
from eNMS.functions import fetch, fetch_all, get, get_one, post
from eNMS.properties import subtype_sizes, link_subtype_to_color, table_properties
from eNMS.views import bp


@get(bp, "/<view_type>_view", "View")
def view(view_type: str) -> dict:
    return dict(
        template="geographical_view",
        parameters=get_one("Parameters").serialized,
        subtype_sizes=subtype_sizes,
        link_colors=link_subtype_to_color,
        view_type=view_type,
    )


@post(bp, "/filtering/<filter_type>")
def filtering(filter_type: str):
    model = filter_type.split("_")[0]
    model, properties = classes[model], table_properties[model]
    constraints = []
    for property in properties:
        value = request.args.get(f"form[{property}]")
        if not value:
            continue
        else:
            constraints.append(getattr(model, property).contains(value))
    result = db.session.query(model).filter(and_(*constraints))
    search_text = request.args.get("form[{configuration}]")
    if search_text:
        result = result.filter(model.current_configuration.contains(search_text))
    pools = [int(id) for id in request.args.getlist("form[pools][]")]
    if pools:
        result = result.filter(model.pools.any(classes["pool"].id.in_(pools)))
    return {}


@post(bp, "/get_logs/<int:device_id>", "View")
def get_logs(device_id: int) -> Union[str, bool]:
    device_logs = [
        log.content
        for log in fetch_all("Log")
        if log.source == fetch("Device", id=device_id).ip_address
    ]
    return "\n".join(device_logs) or True

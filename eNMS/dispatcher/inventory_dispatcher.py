from datetime import datetime
from difflib import SequenceMatcher
from flask import current_app as app, request
from flask_login import current_user
from sqlalchemy import and_
from subprocess import Popen
from typing import Union

from eNMS.database import fetch, fetch_all, get_one, objectify
from eNMS.models import classes
from eNMS.modules import db
from eNMS.properties import link_subtype_to_color, subtype_sizes, table_properties


class InventoryDispatcher:
    def clear_configurations(self, device_id: int) -> None:
        fetch("Device", id=device_id).configurations = {}

    def connection(self, device_id: int) -> dict:
        parameters, device = get_one("Parameters"), fetch("Device", id=device_id)
        cmd = [str(app.path / "applications" / "gotty"), "-w"]
        port, protocol = parameters.get_gotty_port(), request.form["protocol"]
        address = getattr(device, request.form["address"])
        cmd.extend(["-p", str(port)])
        if "accept-once" in request.form:
            cmd.append("--once")
        if "multiplexing" in request.form:
            cmd.extend(f"tmux new -A -s gotty{port}".split())
        if app.config["GOTTY_BYPASS_KEY_PROMPT"]:
            options = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
        else:
            options = ""
        if protocol == "telnet":
            cmd.extend(f"telnet {address}".split())
        elif "authentication" in request.form:
            if request.form["credentials"] == "device":
                login, pwd = device.username, device.password
            else:
                login, pwd = current_user.name, current_user.password
            cmd.extend(f"sshpass -p {pwd} ssh {options} {login}@{address}".split())
        else:
            cmd.extend(f"ssh {options} {address}".split())
        if protocol != "telnet":
            cmd.extend(f"-p {device.port}".split())
        Popen(cmd)
        return {
            "device": device.name,
            "port": port,
            "redirection": app.config["GOTTY_PORT_REDIRECTION"],
            "server_addr": app.config["ENMS_SERVER_ADDR"],
        }

    def get_configurations(self, device_id: int) -> dict:
        return fetch("Device", id=device_id).get_configurations()

    def get_configuration_diff(self, device_id: int, v1: str, v2: str) -> dict:
        device = fetch("Device", id=device_id)
        d1, d2 = [datetime.strptime(d, "%Y-%m-%d %H:%M:%S.%f") for d in (v1, v2)]
        first = device.configurations[d1].splitlines()
        second = device.configurations[d2].splitlines()
        opcodes = SequenceMatcher(None, first, second).get_opcodes()
        return {"first": first, "second": second, "opcodes": opcodes}

    def get_device_logs(self, device_id: int) -> Union[str, bool]:
        device_logs = [
            log.content
            for log in fetch_all("Log")
            if log.source == fetch("Device", id=device_id).ip_address
        ]
        return "\n".join(device_logs)

    def save_pool_objects(self, pool_id: int) -> dict:
        pool = fetch("Pool", id=pool_id)
        pool.devices = objectify("Device", request.form["devices"])
        pool.links = objectify("Link", request.form["links"])
        return pool.serialized

    def update_pools(self, pool_id: str) -> None:
        if pool_id == "all":
            for pool in fetch_all("Pool"):
                pool.compute_pool()
        else:
            fetch("Pool", id=int(pool_id)).compute_pool()

    def view(self, view_type: str) -> dict:
        return dict(
            template="pages/geographical_view",
            parameters=get_one("Parameters").serialized,
            subtype_sizes=subtype_sizes,
            link_colors=link_subtype_to_color,
            view_type=view_type,
        )

    def get_view_topology(self) -> dict:
        return {
            "devices": [d.view_properties for d in fetch_all("Device")],
            "links": [d.view_properties for d in fetch_all("Link")],
        }

    def view_filtering(self, filter_type: str):
        obj_type = filter_type.split("_")[0]
        model = classes[obj_type]
        properties = table_properties[obj_type]
        if obj_type == "device":
            properties.append("current_configuration")
        constraints = []
        for property in properties:
            value = request.form[property]
            if value:
                constraints.append(getattr(model, property).contains(value))
        result = db.session.query(model).filter(and_(*constraints))
        pools = [int(id) for id in request.args.getlist("form[pools][]")]
        if pools:
            result = result.filter(model.pools.any(classes["pool"].id.in_(pools)))
        return [d.view_properties for d in result.all()]

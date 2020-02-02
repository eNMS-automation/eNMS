from collections import Counter
from flask_login import current_user
from logging import info
from sqlalchemy import and_
from subprocess import Popen
from threading import Thread
from uuid import uuid4
from werkzeug.utils import secure_filename
from xlrd import open_workbook
from xlrd.biffh import XLRDError
from xlwt import Workbook

from eNMS.controller.base import BaseController
from eNMS.controller.ssh import SshConnection
from eNMS.database import Session
from eNMS.database.functions import delete_all, factory, fetch, fetch_all, objectify
from eNMS.models import models, model_properties, property_types
from eNMS.properties import field_conversion


class InventoryController(BaseController):

    ssh_port = -1

    def get_ssh_port(self):
        self.ssh_port += 1
        start = self.settings["ssh"]["start_port"]
        end = self.settings["ssh"]["end_port"]
        return start + self.ssh_port % (end - start)

    def connection(self, device_id, **kwargs):
        device = fetch("device", id=device_id)
        cmd = [str(self.path / "files" / "apps" / "gotty"), "-w"]
        port, protocol = self.get_ssh_port(), kwargs["protocol"]
        address = getattr(device, kwargs["address"])
        cmd.extend(["-p", str(port)])
        if "accept-once" in kwargs:
            cmd.append("--once")
        if "multiplexing" in kwargs:
            cmd.extend(f"tmux new -A -s gotty{port}".split())
        if self.settings["ssh"]["bypass_key_prompt"]:
            options = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
        else:
            options = ""
        if protocol == "telnet":
            cmd.extend(f"telnet {address}".split())
        elif "authentication" in kwargs:
            if kwargs["credentials"] == "device":
                login, pwd = device.username, device.password
            else:
                login, pwd = kwargs["user"].name, kwargs["user"].password
            cmd.extend(f"sshpass -p {pwd} ssh {options} {login}@{address}".split())
        else:
            cmd.extend(f"ssh {options} {address}".split())
        if protocol != "telnet":
            cmd.extend(f"-p {device.port}".split())
        Popen(cmd)
        return {
            "device": device.name,
            "port": port,
            "redirection": self.settings["ssh"]["port_redirection"],
            "server_addr": self.settings["app"]["address"],
        }

    def get_device_logs(self, device_id):
        device_logs = [
            log.name
            for log in fetch_all("log")
            if log.source == fetch("device", id=device_id).ip_address
        ]
        return "\n".join(device_logs)

    def handoffssh(self, id, **kwargs):
        device = fetch("device", id=id)
        credentials = (
            (device.username, device.password)
            if kwargs["credentials"] == "device"
            else self.get_user_credentials()
            if kwargs["credentials"] == "user"
            else (kwargs["username"], kwargs["password"])
        )
        uuid, port = str(uuid4()), self.get_ssh_port()
        session = factory(
            "session",
            name=uuid,
            user=current_user.name,
            timestamp=self.get_time(),
            device=device.id,
        )
        Session.commit()
        Thread(
            target=SshConnection,
            args=(device.ip_address, *credentials, session.id, uuid, port),
        ).start()
        return {
            "port": port,
            "username": uuid,
            "device_name": device.name,
            "device_ip": device.ip_address,
        }

    def get_device_network_data(self, device_id):
        device = fetch("device", id=device_id)
        return {"configuration": device.configuration, "data": device.operational_data}

    def get_session_log(self, session_id):
        return fetch("session", id=session_id).content

    def counters(self, property, type):
        return Counter(str(getattr(instance, property)) for instance in fetch_all(type))

    def export_topology(self, **kwargs):
        workbook = Workbook()
        filename = kwargs["export_filename"]
        if "." not in filename:
            filename += ".xls"
        for obj_type in ("device", "link"):
            sheet = workbook.add_sheet(obj_type)
            for index, property in enumerate(model_properties[obj_type]):
                sheet.write(0, index, property)
                for obj_index, obj in enumerate(fetch_all(obj_type), 1):
                    sheet.write(obj_index, index, getattr(obj, property))
        workbook.save(self.path / "files" / "spreadsheets" / filename)

    def topology_import(self, file):
        book = open_workbook(file_contents=file.read())
        status = "Topology successfully imported."
        for obj_type in ("device", "link"):
            try:
                sheet = book.sheet_by_name(obj_type)
            except XLRDError:
                continue
            properties = sheet.row_values(0)
            for row_index in range(1, sheet.nrows):
                values = {"dont_update_pools": True}
                for index, property in enumerate(properties):
                    func = field_conversion[property_types[property]]
                    values[property] = func(sheet.row_values(row_index)[index])
                try:
                    factory(obj_type, **values).serialized
                except Exception as e:
                    info(f"{str(values)} could not be imported ({str(e)})")
                    status = "Partial import (see logs)."
            Session.commit()
        for pool in fetch_all("pool"):
            pool.compute_pool()
        self.log("info", status)
        return status

    def import_topology(self, **kwargs):
        file = kwargs["file"]
        if kwargs["replace"]:
            delete_all("device")
            Session.commit()
        if self.allowed_file(secure_filename(file.filename), {"xls", "xlsx"}):
            result = self.topology_import(file)
        info("Inventory import: Done.")
        return result

    def save_pool_objects(self, pool_id, **kwargs):
        pool = fetch("pool", id=pool_id)
        for obj_type in ("device", "link"):
            string_objects = kwargs[f"string_{obj_type}s"]
            if string_objects:
                objects = []
                for name in [obj.strip() for obj in string_objects.split(",")]:
                    obj = fetch(obj_type, allow_none=True, name=name)
                    if not obj:
                        return {
                            "alert": f"{obj_type.capitalize()} '{name}' does not exist."
                        }
                    if obj not in objects:
                        objects.append(obj)
            else:
                objects = objectify(obj_type, kwargs[f"{obj_type}s"])
            setattr(pool, f"{obj_type}_number", len(objects))
            setattr(pool, f"{obj_type}s", objects)
        return pool.serialized

    def update_pool(self, pool_id):
        fetch("pool", id=int(pool_id)).compute_pool()

    def update_all_pools(self):
        for pool in fetch_all("pool"):
            pool.compute_pool()

    def get_view_topology(self):
        return {
            "devices": [d.view_properties for d in fetch_all("device")],
            "links": [d.view_properties for d in fetch_all("link")],
        }

    def view_filtering(self, obj_type, **kwargs):
        constraints = self.build_filtering_constraints(obj_type, **kwargs)
        result = Session.query(models[obj_type]).filter(and_(*constraints))
        return [d.view_properties for d in result.all()]

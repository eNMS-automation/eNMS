from collections import Counter
from flask_login import current_user
from git import Repo
from io import BytesIO
from logging import info
from os import getenv
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
from eNMS.database import db
from eNMS.models import models, model_properties, property_types


class InventoryController(BaseController):

    ssh_port = -1
    configuration_properties = {"configuration": "Configuration"}
    configuration_timestamps = ("status", "update", "failure", "runtime", "duration")

    def get_ssh_port(self):
        if self.redis_queue:
            self.ssh_port = self.redis("incr", "ssh_port", 1)
        else:
            self.ssh_port += 1
        start = self.settings["ssh"]["start_port"]
        end = self.settings["ssh"]["end_port"]
        return start + int(self.ssh_port) % (end - start)

    def get_credentials(self, device, **kwargs):
        if kwargs["credentials"] == "device":
            credentials = device.get_credentials("any")
            return credentials.username, self.get_password(credentials.password)
        elif kwargs["credentials"] == "user":
            return current_user.name, self.get_password(current_user.password)
        else:
            return kwargs["username"], kwargs["password"]

    def web_connection(self, device_id, **kwargs):
        if not self.settings["ssh"]["credentials"][kwargs["credentials"]]:
            return {"alert": "Unauthorized authentication method."}
        device = db.fetch("device", id=device_id, rbac="connect")
        port, endpoint = self.get_ssh_port(), str(uuid4())
        command = f"flask run -h 0.0.0.0 -p {port}".split()
        if self.settings["ssh"]["bypass_key_prompt"]:
            options = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
        else:
            options = ""
        environment = {
            "DEVICE": str(device.id),
            "ENDPOINT": endpoint,
            "FLASK_APP": "app.py",
            "IP_ADDRESS": getattr(device, kwargs["address"]),
            "OPTIONS": options,
            "PORT": str(device.port),
            "PROTOCOL": kwargs["protocol"],
            "USER": current_user.name,
            "ENMS_USER": getenv("ENMS_USER", "admin"),
            "ENMS_PASSWORD": getenv("ENMS_PASSWORD", "admin"),
        }
        if "authentication" in kwargs:
            credentials = self.get_credentials(device, **kwargs)
            environment.update(zip(("USERNAME", "PASSWORD"), credentials))
        Popen(command, cwd=self.path / "terminal", env=environment)
        return {
            "device": device.name,
            "port": port,
            "endpoint": endpoint,
            "redirection": self.settings["ssh"]["port_redirection"],
        }

    def desktop_connection(self, id, **kwargs):
        if not self.settings["ssh"]["credentials"][kwargs["credentials"]]:
            return {"alert": "Unauthorized authentication method."}
        device = db.fetch("device", id=id, rbac="connect")
        uuid, port = str(uuid4()), self.get_ssh_port()
        session = db.factory(
            "session",
            name=uuid,
            user=current_user.name,
            timestamp=self.get_time(),
            device=device.id,
        )
        db.session.commit()
        try:
            credentials = self.get_credentials(device, **kwargs)
            args = (session.id, uuid, port)
            ssh_connection = SshConnection(device.ip_address, credentials, *args)
            Thread(target=ssh_connection.start_session, args=args).start()
            return {
                "port": port,
                "username": uuid,
                "device_name": device.name,
                "device_ip": device.ip_address,
            }
        except Exception as exc:
            return {"error": exc.args}

    def get_device_logs(self, device_id):
        device_logs = [
            log.name
            for log in db.fetch_all("log")
            if log.source == db.fetch("device", id=device_id).ip_address
        ]
        return "\n".join(device_logs)

    def get_git_history(self, device_id):
        device = db.fetch("device", id=device_id)
        repo = Repo(self.path / "network_data")
        path = self.path / "network_data" / device.name
        return {
            data_type: [
                {"hash": str(commit), "date": commit.committed_datetime}
                for commit in list(repo.iter_commits(paths=path / data_type))
            ]
            for data_type in self.configuration_properties
        }

    def get_git_network_data(self, device_name, hash):
        commit, result = Repo(self.path / "network_data").commit(hash), {}
        device = db.fetch("device", name=device_name)
        for property in self.configuration_properties:
            try:
                file = commit.tree / device_name / property
                with BytesIO(file.data_stream.read()) as f:
                    value = f.read().decode("utf-8")
                result[property] = self.parse_configuration_property(
                    device, property, value
                )
            except KeyError:
                result[property] = ""
        return result, commit.committed_datetime

    def get_device_network_data(self, device_id):
        device = db.fetch("device", id=device_id)
        return {
            property: self.parse_configuration_property(device, property)
            for property in self.configuration_properties
        }

    def get_session_log(self, session_id):
        return db.fetch("session", id=session_id).content

    def counters(self, property, model):
        return Counter(v for v, in db.session.query(getattr(models[model], property)))

    def export_topology(self, **kwargs):
        workbook = Workbook()
        filename = kwargs["export_filename"]
        if "." not in filename:
            filename += ".xls"
        for obj_type in ("device", "link"):
            sheet = workbook.add_sheet(obj_type)
            for index, property in enumerate(model_properties[obj_type]):
                if property in db.dont_migrate[obj_type]:
                    continue
                sheet.write(0, index, property)
                for obj_index, obj in enumerate(db.fetch_all(obj_type), 1):
                    value = getattr(obj, property)
                    if type(value) == bytes:
                        value = str(self.decrypt(value), "utf-8")
                    sheet.write(obj_index, index, str(value))
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
                values = {}
                for index, property in enumerate(properties):
                    if not property:
                        continue
                    func = db.field_conversion[property_types.get(property, "str")]
                    values[property] = func(sheet.row_values(row_index)[index])
                try:
                    db.factory(obj_type, **values).serialized
                except Exception as exc:
                    info(f"{str(values)} could not be imported ({str(exc)})")
                    status = "Partial import (see logs)."
            db.session.commit()
        for pool in db.fetch_all("pool"):
            pool.compute_pool()
        self.log("info", status)
        return status

    def import_topology(self, **kwargs):
        file = kwargs["file"]
        if kwargs["replace"]:
            db.delete_all("device")
        if self.allowed_file(secure_filename(file.filename), {"xls", "xlsx"}):
            result = self.topology_import(file)
        info("Inventory import: Done.")
        return result

    def update_pool(self, pool_id):
        db.fetch("pool", id=int(pool_id)).compute_pool()

    def update_all_pools(self):
        for pool in db.fetch_all("pool"):
            pool.compute_pool()

    def view_filtering(self, **kwargs):
        return {
            f"{model}s": [
                instance.view_properties
                for instance in db.session.query(models[model])
                .filter(and_(*self.build_filtering_constraints(model, **form)))
                .all()
            ]
            for model, form in kwargs.items()
        }

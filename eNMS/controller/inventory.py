from collections import Counter
from datetime import datetime
from flask_login import current_user
from git import Repo
from io import BytesIO
from logging import info
from uuid import uuid4
from xlrd import open_workbook
from xlrd.biffh import XLRDError
from xlwt import Workbook


from eNMS.controller.base import BaseController
from eNMS.database import db
from eNMS.models import models, model_properties, property_types
from eNMS.setup import properties


class InventoryController(BaseController):

    ssh_sessions = {}
    configuration_properties = {"configuration": "Configuration"}
    configuration_timestamps = ("status", "update", "failure", "runtime", "duration")

    def add_objects_to_view(self, view_id, **kwargs):
        result = {"update_time": self.get_time()}
        for model in ("node", "line"):
            base_model = "device" if model == "node" else "link"
            result[f"{model}s"] = []
            for model_id in kwargs[f"{base_model}s"]:
                node = db.factory(model, device=model_id, view=view_id)
                result[f"{model}s"].append(node.serialized)
        return result

    def create_view_object(self, type, view_id, **kwargs):
        node = db.factory(type, view=view_id, **kwargs)
        db.session.flush()
        return {"time": self.get_time(), "node": node.serialized}

    def delete_view_selection(self, selection):
        for instance_id in selection:
            db.delete("view_object", id=instance_id)
        return self.get_time()

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
        session = str(uuid4())
        device = db.fetch("device", id=device_id, rbac="connect")
        self.ssh_sessions[session] = {"device": device.id, "form": kwargs}
        if "authentication" in kwargs:
            credentials = self.get_credentials(device, **kwargs)
            self.ssh_sessions[session]["credentials"] = credentials
        return {"device": device.name, "session": session}

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

    def count_models(self):
        return {
            "counters": {
                model: db.query(model, rbac=None)
                .with_entities(models[model].id)
                .count()
                for model in properties["dashboard"]
            },
            "properties": {
                model: self.counters(properties["dashboard"][model][0], model)
                for model in properties["dashboard"]
            },
        }

    def counters(self, property, model):
        return Counter(v for v, in db.query(model, property=property, rbac=None))

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
        result = self.topology_import(file)
        info("Inventory import: Done.")
        return result

    def save_session(self, session_id, **kwargs):
        session = self.ssh_sessions.pop(session_id, None)
        if session:
            db.factory(
                "session",
                content=kwargs["content"],
                name=str(uuid4()),
                device=session["device"],
                timestamp=str(datetime.now()),
                user=current_user.name,
            )

    def save_view_positions(self, **kwargs):
        for node_id, position in kwargs.items():
            db.factory("view_object", id=node_id, **position)
        return self.get_time()

    def update_pool(self, pool_id):
        db.fetch("pool", id=int(pool_id)).compute_pool()

    def update_all_pools(self):
        for pool in db.fetch_all("pool"):
            pool.compute_pool()

    def view_filtering(self, **kwargs):
        return {
            f"{model}s": self.filtering(model, **kwargs[model], bulk="view_properties")
            for model, form in kwargs.items()
        }

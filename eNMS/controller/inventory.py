from collections import Counter
from flask_login import current_user
from git import Repo
from io import BytesIO
from logging import info
from uuid import uuid4
from xlrd import open_workbook
from xlrd.biffh import XLRDError
from xlwt import Workbook

from eNMS import app
from eNMS.database import db
from eNMS.models import models, model_properties, property_types
from eNMS.setup import properties


class InventoryController:
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
        self.ssh_sessions[session] = {
            "device": device.id,
            "form": kwargs,
            "user": current_user.name,
        }
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

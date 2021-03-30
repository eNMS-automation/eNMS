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

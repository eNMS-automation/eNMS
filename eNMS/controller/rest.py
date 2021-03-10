from collections import defaultdict
from traceback import format_exc
from uuid import getnode

from eNMS.controller.base import BaseController
from eNMS.database import db


class RestController(BaseController):
    def instance(self, model, **data):
        result = defaultdict(list)
        if not isinstance(data, list):
            data = [data]
        for instance in data:
            if "name" not in instance:
                result["failure"].append((instance, "Name is missing"))
                continue
            try:
                object_data = self.objectify(model, instance)
                object_data["update_pools"] = instance.get("update_pools", True)
                instance = db.factory(model, **object_data)
                result["success"].append(instance.name)
            except Exception:
                result["failure"].append((instance, format_exc()))
        return result

    def is_alive(self):
        return {
            "name": getnode(),
            "cluster_id": self.settings["cluster"]["id"],
        }
from collections import defaultdict
from traceback import format_exc
from uuid import getnode

from eNMS import app
from eNMS.database import db


class RestApi():

    rest_routes = {
        "GET": {
            "instance": "get_instance",
            "is_alive": "is_alive",
            "query": "query"
        },
        "POST": {
            "instance": "update_instance"
        },
        "DELETE": {
            "instance": "delete_instance"
        }
    }

    def get_instance(self, model, name):
        return db.fetch(model, name=name).to_dict(
            relation_names_only=True, exclude=["positions"]
        )

    def delete_instance(self, model, name):
        return db.delete(model, name=name)

    def update_instance(self, model, **data):
        result = defaultdict(list)
        if not isinstance(data, list):
            data = [data]
        for instance in data:
            if "name" not in instance:
                result["failure"].append((instance, "Name is missing"))
                continue
            try:
                object_data = app.objectify(model, instance)
                object_data["update_pools"] = instance.get("update_pools", True)
                instance = db.factory(model, **object_data)
                result["success"].append(instance.name)
            except Exception:
                result["failure"].append((instance, format_exc()))
        return result

    def is_alive(self):
        return {
            "name": getnode(),
            "cluster_id": app.settings["cluster"]["id"],
        }

    def query(self, model, **kwargs):
        results = db.fetch(model, all_matches=True, **kwargs)
        return [
            result.get_properties(exclude=["positions"]) for result in results
        ]

from collections import defaultdict
from traceback import format_exc
from uuid import getnode

from eNMS import app
from eNMS.database import db


class RestApi:

    rest_routes = {
        "GET": {
            "configuration": "get_configuration",
            "instance": "get_instance",
            "is_alive": "is_alive",
            "query": "query",
            "result": "get_result",
        },
        "POST": {
            "instance": "update_instance",
            "migrate": "migrate",
        },
        "DELETE": {
            "instance": "delete_instance",
        },
    }

    def get_configuration(self, device_name, property="configuration"):
        return getattr(db.fetch("device", name=device_name), property)

    def get_instance(self, model, name):
        return db.fetch(model, name=name).to_dict(
            relation_names_only=True, exclude=["positions"]
        )

    def get_result(self, name, runtime, **kwargs):
        run = db.fetch("run", service_name=name, runtime=runtime, allow_none=True)
        if not run:
            error_message = (
                "There are no results or on-going services "
                "for the requested service and runtime."
            )
            return {"error": error_message}
        else:
            result = run.result()
            return {
                "status": run.status,
                "result": result.result if result else "No results yet.",
            }

    def delete_instance(self, model, name):
        return db.delete(model, name=name)

    def migrate(self, direction, **kwargs):
        return getattr(app, f"migration_{direction}")(**kwargs)

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
        return [result.get_properties(exclude=["positions"]) for result in results]

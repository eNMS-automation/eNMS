from collections import defaultdict
from flask_login import current_user
from threading import Thread
from traceback import format_exc
from uuid import getnode

from eNMS.controller import controller
from eNMS.database import db
from eNMS.environment import env
from eNMS.variables import vs


class RestApi:
    rest_endpoints = {
        "GET": {
            "configuration": "get_configuration",
            "instance": "get_instance",
            "is_alive": "is_alive",
            "query": "query",
            "result": "get_result",
            "workers": "get_workers",
        },
        "POST": {
            "instance": "update_instance",
            "migrate": "migrate",
            "run_service": "run_service",
            "run_task": "run_task",
            "search": "search",
            "topology": "topology",
        },
        "DELETE": {
            "instance": "delete_instance",
        },
    }

    allowed_endpoints = [
        "get_cluster_status",
        "get_git_content",
        "update_all_pools",
        "update_database_configurations_from_git",
        "update_device_rbac",
    ]

    def __init__(self):
        for endpoint in self.allowed_endpoints:
            self.rest_endpoints["POST"][endpoint] = endpoint
            setattr(self, endpoint, getattr(controller, endpoint))

    def delete_instance(self, instance_type, name):
        return db.delete(instance_type, name=name)

    def get_configuration(self, device_name, property="configuration", **_):
        return getattr(db.fetch("device", name=device_name), property)

    def get_instance(self, instance_type, name, **_):
        return db.fetch(instance_type, name=name).to_dict(
            relation_names_only=True, exclude=["positions"]
        )

    def get_result(self, name, runtime, **_):
        run = db.fetch("run", service_name=name, runtime=runtime, allow_none=True)
        if not run:
            error_message = (
                "There are no results or on-going services "
                "for the requested service and runtime."
            )
            return {"error": error_message}
        else:
            result = db.fetch("result", runtime=runtime, allow_none=True)
            return {
                "status": run.status,
                "result": result.result if result else "No results yet.",
            }

    def get_workers(self):
        return env.get_workers()

    def is_alive(self, **_):
        return {"name": getnode(), "cluster_id": vs.settings["cluster"]["id"]}

    def migrate(self, direction, **kwargs):
        return getattr(controller, f"migration_{direction}")(**kwargs)

    def query(self, instance_type, **kwargs):
        results = db.fetch(instance_type, all_matches=True, **kwargs)
        return [result.get_properties(exclude=["positions"]) for result in results]

    def run_service(self, **kwargs):
        data = {"trigger": "REST API", "creator": current_user.name, **kwargs}
        errors, devices, pools = [], [], []
        service = db.fetch("service", name=data.pop("name"), rbac="run")
        if service.disabled:
            return {"error": "The workflow is disabled."}
        service.check_restriction_to_owners("run")
        run_name = kwargs.get("form", {}).get("name")
        if run_name and db.fetch("run", name=run_name, allow_none=True, rbac=None):
            return {"error": "There is already a run with the same name."}
        handle_asynchronously = data.get("async", True)
        for device_name in data.get("devices", ""):
            device = db.fetch("device", name=device_name, allow_none=True)
            if device:
                devices.append(device.id)
            else:
                errors.append(f"No device with the name '{device_name}'")
        for device_ip in data.get("ip_addresses", ""):
            device = db.fetch("device", ip_address=device_ip, allow_none=True)
            if device:
                devices.append(device.id)
            else:
                errors.append(f"No device with the IP address '{device_ip}'")
        for pool_name in data.get("pools", ""):
            pool = db.fetch("pool", name=pool_name, allow_none=True)
            if pool:
                pools.append(pool.id)
            else:
                errors.append(f"No pool with the name '{pool_name}'")
        if errors and not kwargs.get("ignore_invalid_targets"):
            return {"errors": errors}
        if devices or pools:
            data.update({"target_devices": devices, "target_pools": pools})
        data["runtime"] = runtime = vs.get_time()
        if handle_asynchronously:
            if vs.settings["automation"]["use_task_queue"]:
                controller.run.send(service.id, **data)
            else:
                Thread(target=controller.run, args=(service.id,), kwargs=data).start()
            return {"errors": errors, "runtime": runtime}
        else:
            return {**controller.run(service.id, **data), "errors": errors}

    def run_task(self, task_id):
        task = db.fetch("task", rbac="edit", id=task_id)
        data = {
            "trigger": "Scheduler",
            "creator": task.last_scheduled_by,
            "runtime": vs.get_time(),
            "task": task.id,
            **task.initial_payload,
        }
        if task.devices:
            data["target_devices"] = [device.id for device in task.devices]
        if task.pools:
            data["target_pools"] = [pool.id for pool in task.pools]

        if vs.settings["automation"]["use_task_queue"]:
            controller.run.send(task.service.id, **data)
        else:
            Thread(target=controller.run, args=(task.service.id,), kwargs=data).start()

    def search(self, **kwargs):
        filtering_kwargs = {
            "draw": 1,
            "columns": [{"data": column} for column in kwargs["columns"]],
            "order": kwargs.get("order", [{"column": 0, "dir": "asc"}]),
            "start": kwargs.get("start", 0),
            "length": kwargs.get("maximum_return_records", 10),
            "form": kwargs.get("search_criteria", {}),
            "rest_api_request": True,
        }
        return controller.filtering(kwargs["type"], **filtering_kwargs)["data"]

    def topology(self, direction, **kwargs):
        if direction == "import":
            result = controller.import_topology(
                **{
                    "replace": kwargs["replace"] == "True",
                    "file": kwargs["file"],
                }
            )
            return result, 206 if "Partial" in result else 200
        else:
            controller.topology_export(**kwargs)
            return "Topology Export successfully executed."

    def update_instance(self, instance_type, list_data=None, **data):
        result, data = defaultdict(list), list_data or [data]
        for instance in data:
            if "name" not in instance:
                result["failure"].append((instance, "Name is missing"))
                continue
            try:
                new_name = instance.pop("new_name", None)
                object_data = controller.objectify(instance_type, instance)
                instance = db.factory(instance_type, **object_data)
                if new_name:
                    instance.name = new_name
                result["success"].append(instance.name)
            except Exception:
                result["failure"].append((instance, format_exc()))
        return result

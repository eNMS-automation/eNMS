from collections import defaultdict
from flask_login import current_user
from threading import Thread
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
            "run_service": "run_service",
            "run_task": "run_task",
        },
        "DELETE": {
            "instance": "delete_instance",
        },
    }

    def process(self, method, endpoint, args, kwargs):
        function = getattr(self, self.rest_routes[method][endpoint])
        if not isinstance(kwargs, dict):
            args, kwargs = args + [kwargs], {}
        return function(*args, **kwargs)

    def get_configuration(self, device_name, property="configuration"):
        return getattr(db.fetch("device", name=device_name), property)

    def get_instance(self, model, name):
        return db.fetch(model, name=name).to_dict(
            relation_names_only=True, exclude=["positions"]
        )

    def get_result(self, name, runtime):
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

    def run_service(self, **kwargs):
        data = {"trigger": "REST", "creator": current_user.name, **kwargs}
        errors, devices, pools = [], [], []
        service = db.fetch("service", name=data["name"], rbac="run")
        handle_asynchronously = data.get("async", False)
        for device_name in data.get("devices", ""):
            device = db.fetch("device", name=device_name)
            if device:
                devices.append(device.id)
            else:
                errors.append(f"No device with the name '{device_name}'")
        for device_ip in data.get("ip_addresses", ""):
            device = db.fetch("device", ip_address=device_ip)
            if device:
                devices.append(device.id)
            else:
                errors.append(f"No device with the IP address '{device_ip}'")
        for pool_name in data.get("pools", ""):
            pool = db.fetch("pool", name=pool_name)
            if pool:
                pools.append(pool.id)
            else:
                errors.append(f"No pool with the name '{pool_name}'")
        if errors:
            return {"errors": errors}
        if devices or pools:
            data.update({"target_devices": devices, "target_pools": pools})
        data["runtime"] = runtime = app.get_time()
        if handle_asynchronously:
            Thread(target=app.run, args=(service.id,), kwargs=data).start()
            return {"errors": errors, "runtime": runtime}
        else:
            return {**app.run(service.id, **data), "errors": errors}

    def run_task(self, task_id):
        task = db.fetch("task", rbac="schedule", id=task_id)
        data = {
            "trigger": "Scheduler",
            "creator": task.last_scheduled_by,
            "runtime": app.get_time(),
            "task": task.id,
            **task.initial_payload,
        }
        if task.devices:
            data["target_devices"] = [device.id for device in task.devices]
        if task.pools:
            data["target_pools"] = [pool.id for pool in task.pools]
        Thread(target=app.run, args=(task.service.id,), kwargs=data).start()

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

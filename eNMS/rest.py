from datetime import datetime
from flask import Flask, request
from flask_restful import Api, Resource
from logging import info
from psutil import cpu_percent
from uuid import getnode
from typing import Optional, Union

from eNMS.concurrency import threaded_job
from eNMS.controller import controller
from eNMS.database import Session
from eNMS.database.functions import delete, factory, fetch
from eNMS.exceptions import InstanceNotFoundException
from eNMS.extensions import auth, csrf


class CreatePool(Resource):
    decorators = [auth.login_required]

    def post(self) -> dict:
        data = request.get_json(force=True)
        factory(
            "Pool",
            **{
                "name": data["name"],
                "devices": [
                    fetch("Device", name=name).id for name in data.get("devices", "")
                ],
                "links": [
                    fetch("Link", name=name).id for name in data.get("links", "")
                ],
                "never_update": True,
            },
        )
        Session.commit()
        return data


class Heartbeat(Resource):
    def get(self) -> dict:
        return {
            "name": getnode(),
            "cluster_id": controller.cluster_id,
            "cpu_load": cpu_percent(),
        }


class GetInstance(Resource):
    decorators = [auth.login_required]

    def get(self, cls: str, name: str) -> dict:
        try:
            return fetch(cls, name=name).serialized
        except InstanceNotFoundException:
            return {"error": f"{cls} {name} not found."}

    def delete(self, cls: str, name: str) -> dict:
        result = delete(fetch(cls, name=name))
        Session.commit()
        return result


class GetConfiguration(Resource):
    decorators = [auth.login_required]

    def get(self, name: str) -> str:
        device = fetch("Device", name=name)
        return device.configurations[max(device.configurations)]


class UpdateInstance(Resource):
    decorators = [auth.login_required]

    def post(self, cls: str) -> dict:
        result = factory(cls, **request.get_json(force=True)).serialized
        Session.commit()
        return result


class Migrate(Resource):
    decorators = [auth.login_required]

    def post(self, direction: str) -> Optional[str]:
        return getattr(controller, f"migration_{direction}")(
            **request.get_json(force=True)
        )


class RunJob(Resource):
    decorators = [auth.login_required]

    def post(self) -> Union[str, dict]:
        try:
            errors, targets, data = [], set(), request.get_json(force=True)
            job = fetch("Job", name=data["name"])
            if job.is_running:
                return {"error": "Job is already running."}
            handle_asynchronously = data.get("async", False)
            for device_name in data.get("devices", ""):
                device = fetch("Device", name=device_name)
                if device:
                    targets.add(device)
                else:
                    errors.append(f"No device with the name '{device_name}'")
            for device_ip in data.get("ip_addresses", ""):
                device = fetch("Device", ip_address=device_ip)
                if device:
                    targets.add(device)
                else:
                    errors.append(f"No device with the IP address '{device_ip}'")
            for pool_name in data.get("pools", ""):
                pool = fetch("Pool", name=pool_name)
                if pool:
                    targets |= set(pool.devices)
                else:
                    errors.append(f"No pool with the name '{pool_name}'")
            if errors and not targets:
                return {"errors": errors}
        except Exception as e:
            info(f"REST API run_job endpoint failed ({str(e)})")
            return str(e)
        if handle_asynchronously:
            controller.scheduler.add_job(
                id=controller.get_time(),
                func=threaded_job,
                run_date=datetime.now(),
                args=[job.id, None, [d.id for d in targets], data.get("payload")],
                trigger="date",
            )
            return {**job.serialized, "errors": errors}
        else:
            return {
                **job.run(targets=targets, payload=data.get("payload"))[0],
                "errors": errors,
            }


class Topology(Resource):
    decorators = [auth.login_required]

    def post(self, direction: str) -> Optional[str]:
        if direction == "import":
            return controller.import_topology(
                **{
                    "replace": request.form["replace"] == "True",
                    "file": request.files["file"],
                }
            )
        else:
            controller.export_topology(**request.get_json(force=True))
            return None


def configure_rest_api(app: Flask) -> None:
    api = Api(app, decorators=[csrf.exempt])
    api.add_resource(CreatePool, "/rest/create_pool")
    api.add_resource(Heartbeat, "/rest/is_alive")
    api.add_resource(RunJob, "/rest/run_job")
    api.add_resource(UpdateInstance, "/rest/instance/<string:cls>")
    api.add_resource(GetInstance, "/rest/instance/<string:cls>/<string:name>")
    api.add_resource(GetConfiguration, "/rest/configuration/<string:name>")
    api.add_resource(Migrate, "/rest/migrate/<string:direction>")
    api.add_resource(Topology, "/rest/topology/<string:direction>")

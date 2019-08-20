from datetime import datetime
from flask import Flask, request
from flask_restful import abort, Api, Resource
from logging import info
from psutil import cpu_percent
from uuid import getnode
from typing import Any, Dict, Optional, Union

from eNMS.controller.concurrency import run_job
from eNMS.database import Session
from eNMS.database.functions import delete, factory, fetch
from eNMS.framework.extensions import auth, csrf


def create_controller_resources(controller) -> Dict[str, Resource]:
    endpoints = {}
    for endpoint in controller.valid_rest_endpoints:

        def post(_: Any, ep: str = endpoint) -> str:
            getattr(controller, ep)()
            Session.commit()
            return f"Endpoint {ep} successfully executed."

        endpoints[endpoint] = type(
            endpoint, (Resource,), {"decorators": [auth.login_required], "post": post}
        )
    return endpoints


def create_rest_endpoints(api, controller):
    class CreatePool(Resource):
        decorators = [auth.login_required]

        def post(self) -> dict:
            data = request.get_json(force=True)
            factory(
                "Pool",
                **{
                    "name": data["name"],
                    "devices": [
                        fetch("Device", name=name).id
                        for name in data.get("devices", "")
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

    class Query(Resource):
        decorators = [auth.login_required]

        def get(self, cls: str) -> Union[dict, list]:
            try:
                results = fetch(cls, all_matches=True, **request.args.to_dict())
                return [result.get_properties() for result in results]
            except Exception:
                return abort(404, message=f"There are no such {cls}s.")

    class GetInstance(Resource):
        decorators = [auth.login_required]

        def get(self, cls: str, name: str) -> dict:
            try:
                return fetch(cls, name=name).serialized
            except Exception:
                return abort(404, message=f"{cls} {name} not found.")

        def delete(self, cls: str, name: str) -> dict:
            result = delete(cls, name=name)
            Session.commit()
            return result

    class GetConfiguration(Resource):
        decorators = [auth.login_required]

        def get(self, name: str) -> str:
            device = fetch("Device", name=name)
            return device.configurations[max(device.configurations)]

    class GetResult(Resource):
        decorators = [auth.login_required]

        def get(self, name: str, runtime: str) -> str:
            job = fetch("Job", name=name)
            return fetch("Result", job_id=job.id, runtime=runtime).result

    class UpdateInstance(Resource):
        decorators = [auth.login_required]

        def post(self, cls: str) -> dict:
            try:
                data = request.get_json(force=True)
                object_data = controller.objectify(cls.capitalize(), data)
                result = factory(cls, **object_data).serialized
                Session.commit()
                return result
            except Exception as exc:
                return abort(500, message=f"Update failed ({exc})")

    class Migrate(Resource):
        decorators = [auth.login_required]

        def post(self, direction: str) -> Optional[str]:
            kwargs = request.get_json(force=True)
            return getattr(controller, f"migration_{direction}")(**kwargs)

    class RunJob(Resource):
        decorators = [auth.login_required]

        def post(self) -> Union[str, dict]:
            try:
                errors, data = [], request.get_json(force=True)
                devices, pools = [], []
                job = fetch("Job", name=data["name"])
                handle_asynchronously = data.get("async", False)
                for device_name in data.get("devices", ""):
                    device = fetch("Device", name=device_name)
                    if device:
                        devices.append(device.id)
                    else:
                        errors.append(f"No device with the name '{device_name}'")
                for device_ip in data.get("ip_addresses", ""):
                    device = fetch("Device", ip_address=device_ip)
                    if device:
                        devices.append(device.id)
                    else:
                        errors.append(f"No device with the IP address '{device_ip}'")
                for pool_name in data.get("pools", ""):
                    pool = fetch("Pool", name=pool_name)
                    if pool:
                        pools.append(pool.id)
                    else:
                        errors.append(f"No pool with the name '{pool_name}'")
                if errors:
                    return {"errors": errors}
            except Exception as e:
                info(f"REST API run_job endpoint failed ({str(e)})")
                return str(e)
            if devices or pools:
                data.update({"devices": devices, "pools": pools})
            data["runtime"] = runtime = controller.get_time()
            if handle_asynchronously:
                controller.scheduler.add_job(
                    id=runtime,
                    func=run_job,
                    run_date=datetime.now(),
                    args=[job.id],
                    kwargs=data,
                    trigger="date",
                )
                return {"errors": errors, "runtime": runtime}
            else:
                return {**run_job(job.id, **data), "errors": errors}

    class Topology(Resource):
        decorators = [auth.login_required]

        def post(self, direction: str) -> str:
            if direction == "import":
                return controller.import_topology(
                    **{
                        "replace": request.form["replace"] == "True",
                        "file": request.files["file"],
                    }
                )
            else:
                controller.export_topology(**request.get_json(force=True))
                return "Topology Export successfully executed."

    api.add_resource(CreatePool, "/rest/create_pool")
    api.add_resource(Heartbeat, "/rest/is_alive")
    api.add_resource(RunJob, "/rest/run_job")
    api.add_resource(Query, "/rest/query/<string:cls>")
    api.add_resource(UpdateInstance, "/rest/instance/<string:cls>")
    api.add_resource(GetInstance, "/rest/instance/<string:cls>/<string:name>")
    api.add_resource(GetConfiguration, "/rest/configuration/<string:name>")
    api.add_resource(GetResult, "/rest/result/<string:name>/<string:runtime>")
    api.add_resource(Migrate, "/rest/migrate/<string:direction>")
    api.add_resource(Topology, "/rest/topology/<string:direction>")


def configure_rest_api(app: Flask, controller) -> None:
    api = Api(app, decorators=[csrf.exempt])
    for endpoint, resource in create_controller_resources(controller).items():
        api.add_resource(resource, f"/rest/{endpoint}")
    create_rest_endpoints(api, controller)

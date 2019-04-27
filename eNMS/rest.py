from datetime import datetime
from flask import current_app, Flask, jsonify, make_response, request
from flask_restful import Api, Resource
from flask.wrappers import Response
from logging import info
from psutil import cpu_percent
from uuid import getnode
from typing import Union

from eNMS.extensions import auth, scheduler
from eNMS.admin.functions import migrate_export, migrate_import
from eNMS.automation.functions import scheduler_job
from eNMS.functions import delete, factory, fetch
from eNMS.inventory.functions import object_export, object_import


@auth.get_password
def get_password(username: str) -> str:
    return getattr(fetch("User", name=username), "password", False)


@auth.error_handler
def unauthorized() -> Response:
    return make_response(jsonify({"message": "Unauthorized access"}), 403)


class Heartbeat(Resource):
    def get(self) -> dict:
        return {
            "name": getnode(),
            "cluster_id": current_app.config["CLUSTER_ID"],
            "cpu_load": cpu_percent(),
        }


class RestAutomation(Resource):
    decorators = [auth.login_required]

    def post(self) -> Union[str, dict]:
        try:
            errors, targets, data = [], set(), request.get_json()
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
            scheduler.add_job(
                id=str(datetime.now()),
                func=scheduler_job,
                run_date=datetime.now(),
                args=[job.id, None, [d.id for d in targets], data.get("payload")],
                trigger="date",
            )
            return {**job.serialized, "errors": errors}
        else:
            return {
                **job.try_run(targets=targets, payload=data.get("payload"))[0],
                "errors": errors,
            }


class GetInstance(Resource):
    decorators = [auth.login_required]

    def get(self, cls: str, name: str) -> dict:
        return fetch(cls, name=name).serialized

    def delete(self, cls: str, name: str) -> dict:
        return delete(fetch(cls, name=name))


class GetConfiguration(Resource):
    decorators = [auth.login_required]

    def get(self, name: str) -> str:
        device = fetch("Device", name=name)
        return device.configurations[max(device.configurations)]


class UpdateInstance(Resource):
    decorators = [auth.login_required]

    def post(self, cls: str) -> dict:
        return factory(cls, **request.get_json()).serialized


class Migrate(Resource):
    decorators = [auth.login_required]

    def post(self, direction: str) -> Union[bool, str]:
        args = (current_app, request.get_json())
        return migrate_import(*args) if direction == "import" else migrate_export(*args)


class Topology(Resource):
    decorators = [auth.login_required]

    def post(self, direction: str) -> Union[bool, str]:
        if direction == "import":
            data = request.form.to_dict()
            data["replace"] = True if data["replace"] == "True" else False
            return object_import(data, request.files["file"])
        else:
            return object_export(request.get_json(), current_app.path)


def configure_rest_api(app: Flask) -> None:
    api = Api(app)
    api.add_resource(Heartbeat, "/rest/is_alive")
    api.add_resource(RestAutomation, "/rest/run_job")
    api.add_resource(UpdateInstance, "/rest/instance/<string:cls>")
    api.add_resource(GetInstance, "/rest/instance/<string:cls>/<string:name>")
    api.add_resource(GetConfiguration, "/rest/configuration/<string:name>")
    api.add_resource(Migrate, "/rest/migrate/<string:direction>")
    api.add_resource(Topology, "/rest/topology/<string:direction>")

from datetime import datetime
from flask import current_app, jsonify, make_response, request
from flask_restful import Api, Resource
from psutil import cpu_percent
from uuid import getnode

from eNMS.main import auth, scheduler
from eNMS.admin.helpers import migrate_export, migrate_import
from eNMS.automation.helpers import scheduler_job
from eNMS.base.helpers import delete, factory, fetch
from eNMS.inventory.helpers import object_export, object_import


@auth.get_password
def get_password(username):
    return fetch('User', name=username).password


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'message': 'Unauthorized access'}), 403)


class Heartbeat(Resource):

    def get(self):
        return {
            'name': getnode(),
            'cpu_load': cpu_percent()
        }


class RestAutomation(Resource):
    decorators = [auth.login_required]

    def post(self):
        payload = request.get_json()
        job = fetch('Job', name=payload['name'])
        handle_asynchronously = payload.get('async', True)
        targets = {
            fetch('Device', name=device_name).id
            for device_name in payload.get('devices', '')
        }
        for pool_name in payload.get('pools', ''):
            targets |= {d.id for d in fetch('Pool', name=pool_name).devices}
        if handle_asynchronously:
            scheduler.add_job(
                id=str(datetime.now()),
                func=scheduler_job,
                run_date=datetime.now(),
                args=[job.id],
                trigger='date'
            )
            return job.serialized
        else:
            return job.try_run(targets=targets)[0]


class GetInstance(Resource):
    decorators = [auth.login_required]

    def get(self, cls, name):
        return fetch(cls, name=name).get_properties()

    def delete(self, cls, name):
        return delete(fetch(cls, name=name))


class GetConfiguration(Resource):
    decorators = [auth.login_required]

    def get(self, name):
        device = fetch('Device', name=name)
        return device.configurations[max(device.configurations)]


class UpdateInstance(Resource):
    decorators = [auth.login_required]

    def post(self, cls):
        return factory(cls, **request.get_json()).serialized


class Migrate(Resource):
    decorators = [auth.login_required]

    def post(self, direction):
        return {
            'import': migrate_import,
            'export': migrate_export
        }[direction](current_app.path, request.get_json())


class Topology(Resource):
    decorators = [auth.login_required]

    def post(self, direction):
        if direction == 'import':
            data = request.form.to_dict()
            for property in ('replace', 'update_pools'):
                data[property] = True if data[property] == 'True' else False
            return object_import(data, request.files['file'])
        elif direction == 'export':
            return object_export(request.get_json(), current_app.path)


def configure_rest_api(app):
    api = Api(app)
    api.add_resource(Heartbeat, '/rest/is_alive')
    api.add_resource(RestAutomation, '/rest/run_job')
    api.add_resource(UpdateInstance, '/rest/instance/<string:cls>')
    api.add_resource(GetInstance, '/rest/instance/<string:cls>/<string:name>')
    api.add_resource(GetConfiguration, '/rest/configuration/<string:name>')
    api.add_resource(Migrate, '/rest/migrate/<string:direction>')
    api.add_resource(Topology, '/rest/topology/<string:direction>')

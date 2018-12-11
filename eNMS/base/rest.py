from flask import current_app, jsonify, make_response, request
from flask_restful import Api, Resource
from psutil import cpu_percent

from eNMS import auth
from eNMS.admin.helpers import migrate_export, migrate_import
from eNMS.base.helpers import delete, factory, fetch, get_one
from eNMS.objects.helpers import object_export, object_import


@auth.get_password
def get_password(username):
    return fetch('User', name=username).password


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'message': 'Unauthorized access'}), 403)


class Heartbeat(Resource):

    def get(self):
        parameters = get_one('Parameters')
        return {
            'name': parameters.instance_id,
            'cpu_load': cpu_percent()
        }


class RestAutomation(Resource):
    decorators = [auth.login_required]

    def post(self):
        payload = request.get_json()
        job = fetch('Job', name=payload['name'])
        targets = {
            fetch('Device', name=device_name)
            for device_name in request.get_json().get('devices', '')
        }
        for pool_name in request.get_json().get('pools', ''):
            targets |= set(fetch('Pool', name=pool_name).devices)
        return job.try_run(remaining_targets=targets)


class GetInstance(Resource):
    decorators = [auth.login_required]

    def get(self, cls, name):
        return fetch(cls, name=name).get_properties()

    def delete(self, cls, name):
        return delete(fetch(cls, name=name))


class UpdateInstance(Resource):
    decorators = [auth.login_required]

    def post(self, cls):
        return factory(cls, **request.get_json()).name

    def put(self, cls):
        return self.post(cls)


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
    api.add_resource(UpdateInstance, '/rest/object/<string:cls>')
    api.add_resource(GetInstance, '/rest/object/<string:cls>/<string:name>')
    api.add_resource(Migrate, '/rest/migrate/<string:direction>')
    api.add_resource(Topology, '/rest/topology/<string:direction>')

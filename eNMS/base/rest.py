from flask import current_app, jsonify, make_response, request
from flask_restful import Api, Resource

from eNMS import auth
from eNMS.base.helpers import delete, factory, fetch
from eNMS.base.security import get_user_credentials


@auth.get_password
def get_password(username):
    user = fetch('User', name=username)
    if user:
        return get_user_credentials(current_app, user)[1]


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'message': 'Unauthorized access'}), 403)


class Heartbeat(Resource):

    def get(self):
        return True


class RestAutomation(Resource):
    decorators = [auth.login_required]

    def get(self, job_name):
        job = fetch('Job', name=job_name)
        results = job.run()
        return {'job': job.serialized, 'results': results}


class GetInstance(Resource):
    decorators = [auth.login_required]

    def get(self, cls, name):
        return fetch(cls, name=name).properties

    def delete(self, cls, name):
        return delete(fetch(cls, name=name))


class UpdateInstance(Resource):
    decorators = [auth.login_required]

    def post(self, cls):
        return factory(cls, **request.get_json(force=True, silent=True)).name

    def put(self, cls):
        return self.post(cls)


def configure_rest_api(app):
    api = Api(app)
    api.add_resource(Heartbeat, '/rest/is_alive')
    api.add_resource(RestAutomation, '/rest/run_job/<string:job_name>')
    api.add_resource(UpdateInstance, '/rest/object/<string:cls>')
    api.add_resource(GetInstance, '/rest/object/<string:cls>/<string:name>')

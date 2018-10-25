from flask import current_app, jsonify, make_response, request
from flask_restful import Api, Resource

from eNMS import auth, db
from eNMS.admin.models import User
from eNMS.automation.models import Job
from eNMS.base.classes import diagram_classes
from eNMS.base.custom_base import factory
from eNMS.base.helpers import get_user_credentials, get


@auth.get_password
def get_password(username):
    user = get(User, name=username)
    if user:
        return get_user_credentials(current_app, user)[1]


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'message': 'Unauthorized access'}), 403)


class RestAutomation(Resource):
    decorators = [auth.login_required]

    def get(self, job_name):
        job = get(Job, name=job_name)
        results = job.run()
        return {'job': job.serialized, 'results': results}


class GetInstance(Resource):
    decorators = [auth.login_required]

    def get(self, cls_name, object_name):
        return get(diagram_classes[cls_name], name=object_name).serialized

    def delete(self, cls_name, object_name):
        obj = get(diagram_classes[cls_name], name=object_name)
        db.session.delete(obj)
        db.session.commit()
        return f'{cls_name} {object_name} successfully deleted'


class UpdateInstance(Resource):
    decorators = [auth.login_required]

    def post(self, cls_name):
        return factory(**request.get_json(force=True, silent=True)).serialized

    def put(self, cls_name):
        return self.post(cls_name)


def configure_rest_api(app):
    api = Api(app)
    api.add_resource(
        RestAutomation,
        '/rest/run_job/<string:job_name>'
    )
    api.add_resource(
        UpdateInstance,
        '/rest/object/<string:cls_name>'
    )
    api.add_resource(
        GetInstance,
        '/rest/object/<string:cls_name>/<string:object_name>'
    )

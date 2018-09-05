from flask import request
from flask_restful import Api, Resource

from eNMS import db
from eNMS.base.classes import diagram_classes
from eNMS.base.custom_base import factory
from eNMS.base.helpers import retrieve
from eNMS.tasks.models import Task


class RestAutomation(Resource):

    def get(self, task_name):
        task = retrieve(Task, name=task_name)
        runtime = task.schedule(run_now=True)
        return {'task': task.serialized, 'id': runtime}


class GetObject(Resource):

    def get(self, cls_name, object_name):
        return retrieve(diagram_classes[cls_name], name=object_name).serialized

    def delete(self, cls_name, object_name):
        obj = retrieve(diagram_classes[cls_name], name=object_name)
        db.session.delete(obj)
        db.session.commit()
        return f'{cls_name} {object_name} successfully deleted'


class UpdateObject(Resource):

    def post(self, cls_name):
        return factory(**request.get_json(force=True, silent=True)).serialized

    def put(self, cls_name):
        return self.post(cls_name)


def configure_rest_api(app):
    api = Api(app)
    api.add_resource(
        RestAutomation,
        '/rest/execute_task/<string:task_name>'
    )
    api.add_resource(
        UpdateObject,
        '/rest/object/<string:cls_name>'
    )
    api.add_resource(
        GetObject,
        '/rest/object/<string:cls_name>/<string:object_name>'
    )

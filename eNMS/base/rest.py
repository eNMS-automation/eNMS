from flask import request
from flask_restful import Api, Resource

from eNMS import db
from eNMS.base.classes import class_to_factory, diagram_classes
from eNMS.objects.models import get_obj
from eNMS.tasks.models import Task


class RestAutomation(Resource):

    def get(self, task_name):
        task = get_obj(Task, name=task_name)
        task.run(run_now=True)
        return task.serialized


class GetObject(Resource):

    def get(self, class_name, object_name):
        return get_obj(diagram_classes[class_name], name=object_name).serialized

    def delete(self, class_name, object_name):
        obj = get_obj(diagram_classes[class_name], name=object_name)
        db.session.delete(obj)
        db.session.commit()
        return '{} {} successfully deleted'.format(class_name, object_name)

class UpdateObject(Resource):

    def post(self, class_name):
        body = request.get_json(force=True, silent=True)
        print(body)
        factory = class_to_factory[class_name]
        obj = factory(**body)
        return obj.serialized

    def put(self, class_name):
        self.post(class_name)


def configure_rest_api(app):
    api = Api(app)
    api.add_resource(
        RestAutomation,
        '/rest/execute_task/<string:task_name>'
    )
    api.add_resource(
        UpdateObject,
        '/rest/object/<string:class_name>'
    )
    api.add_resource(
        GetObject,
        '/rest/object/<string:class_name>/<string:object_name>'
    )

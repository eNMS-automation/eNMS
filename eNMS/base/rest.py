from flask_restful import Api, Resource

from eNMS.base.classes import diagram_classes
from eNMS.objects.models import get_obj
from eNMS.tasks.models import Task


class RestAutomation(Resource):

    def get(self, task_name):
        task = get_obj(Task, name=task_name)
        task.run()
        return {'result': task.serialized}


class GetObject(Resource):

    def get(self, class_name, object_name):
        return get_obj(diagram_classes[class_name], name=object_name).serialized


def configure_rest_api(app):
    api = Api(app)
    api.add_resource(
        RestAutomation,
        '/rest/execute_task/<string:task_name>'
    )
    api.add_resource(
        GetObject,
        '/rest/get/<string:class_name>/<string:object_name>'
    )

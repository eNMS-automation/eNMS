from flask_restful import Api, Resource

from eNMS.objects.models import get_obj
from eNMS.tasks.models import Task


class RestAutomation(Resource):

    def get(self, task_name):
        task = get_obj(Task, name=task_name)
        task.run()
        return {'result': task.serialized}


def configure_rest_api(app):
    api = Api(app)
    api.add_resource(
        RestAutomation,
        '/execute_task/<string:task_name>'
    )

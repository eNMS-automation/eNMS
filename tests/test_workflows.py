from time import sleep

from eNMS.base.helpers import retrieve
from eNMS.tasks.models import Task

from tests.test_base import check_blueprints


@check_blueprints('/tasks', '/workflows')
def netmiko_workflow(user_client):
    task = retrieve(Task, name='task_netmiko_VRF_workflow')
    runtime = task.schedule(run_now=True)
    sleep(300)
    assert task.logs[runtime]['success']

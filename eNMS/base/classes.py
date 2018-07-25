from eNMS.admin.models import User, user_factory
from eNMS.objects.models import Link, Node, object_factory, pool_factory
from eNMS.scripts.models import Script, script_factory
from eNMS.tasks.models import Task, task_factory
from eNMS.workflows.models import Workflow, workflow_factory

diagram_classes = {
    'node': Node,
    'link': Link,
    'user': User,
    'script': Script,
    'workflow': Workflow,
    'task': Task
}

class_to_factory = {
    'node': object_factory,
    'link': object_factory,
    'pool': pool_factory,
    'user': user_factory,
    'script': script_factory,
    'task': task_factory,
    'workflow': workflow_factory
}

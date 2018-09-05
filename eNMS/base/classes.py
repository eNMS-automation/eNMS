from eNMS.admin.models import User
from eNMS.base.custom_base import base_factory
from eNMS.objects.models import Link, Node, object_factory
from eNMS.scripts.models import Script, script_factory
from eNMS.tasks.models import Task, task_factory
from eNMS.workflows.models import Workflow

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
    'pool': base_factory,
    'user': base_factory,
    'script': script_factory,
    'task': task_factory,
    'workflow': base_factory
}

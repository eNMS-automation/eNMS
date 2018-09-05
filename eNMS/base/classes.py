from eNMS.admin.models import User
from eNMS.base.custom_base import base_factory
from eNMS.objects.models import Link, Node
from eNMS.scripts.models import Script
from eNMS.tasks.models import Task
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
    'node': base_factory,
    'link': base_factory,
    'pool': base_factory,
    'user': base_factory,
    'script': base_factory,
    'task': base_factory,
    'workflow': base_factory
}

from eNMS.admin.models import User
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

from eNMS.objects.models import Link, Node
from eNMS.tasks.models import Task
from eNMS.workflows.models import Workflow
from eNMS.admin.models import User
from eNMS.scripts.models import Script

diagram_classes = {
    'node': Node,
    'link': Link,
    'user': User,
    'script': Script,
    'workflow': Workflow,
    'task': Task
}

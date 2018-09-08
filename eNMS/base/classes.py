from eNMS.admin.models import User
from eNMS.objects.models import Link, Device
from eNMS.scripts.models import Script
from eNMS.tasks.models import Task
from eNMS.workflows.models import Workflow

diagram_classes = {
    'device': Device,
    'link': Link,
    'user': User,
    'script': Script,
    'workflow': Workflow,
    'task': Task
}

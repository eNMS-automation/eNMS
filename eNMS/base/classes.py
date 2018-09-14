from eNMS.admin.models import User
from eNMS.objects.models import Link, Device
from eNMS.services.models import Service
from eNMS.tasks.models import Task
from eNMS.workflows.models import Workflow

diagram_classes = {
    'device': Device,
    'link': Link,
    'user': User,
    'service': Service,
    'workflow': Workflow,
    'task': Task
}

from eNMS.admin.models import User
from eNMS.objects.models import Link, Device
from eNMS.automation.models import Service, Workflow
from eNMS.tasks.models import Task

diagram_classes = {
    'device': Device,
    'link': Link,
    'user': User,
    'service': Service,
    'workflow': Workflow,
    'task': Task
}

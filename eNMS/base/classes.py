from eNMS.admin.models import User
from eNMS.objects.models import Link, Device, Pool
from eNMS.automation.models import Service, Workflow
from eNMS.scheduling.models import Task

diagram_classes = {
    'device': Device,
    'link': Link,
    'pool': Pool,
    'user': User,
    'service': Service,
    'workflow': Workflow,
    'task': Task
}

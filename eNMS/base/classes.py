from eNMS.admin.models import User
from eNMS.objects.models import Link, Device, Pool
from eNMS.automation.models import Job, Service, Workflow, WorkflowEdge
from eNMS.scheduling.models import Task

classes = {
    'device': Device,
    'edge': WorkflowEdge,
    'link': Link,
    'pool': Pool,
    'user': User,
    'job': Job,
    'service': Service,
    'workflow': Workflow,
    'task': Task
}

diagram_classes = {
    'device': Device,
    'link': Link,
    'pool': Pool,
    'user': User,
    'service': Service,
    'edge': WorkflowEdge,
    'workflow': Workflow,
    'task': Task
}

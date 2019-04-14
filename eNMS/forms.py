from eNMS.admin.forms import InstanceForm, UserForm
from eNMS.automation.forms import JobForm
from eNMS.inventory.forms import (
    ConnectionForm,
    DeviceAutomationForm,
    DeviceForm,
    LinkForm,
    PoolForm,
)
from eNMS.scheduling.forms import TaskForm

form_classes = {
    "connection": ConnectionForm,
    "device": DeviceForm,
    "device_automation": DeviceAutomationForm,
    "instance": InstanceForm,
    "link": LinkForm,
    "pool": PoolForm,
    "user": UserForm,
    "service": JobForm,
    "task": TaskForm,
    "workflow": JobForm,
}

form_templates = {
    "connection": "connection_form",
    "device": "base_form",
    "device_automation": "device_automation_form",
    "instance": "base_form",
    "link": "base_form",
    "pool": "pool_form",
    "service": "service_form",
    "task": "base_form",
    "workflow": "workflow_form",
}

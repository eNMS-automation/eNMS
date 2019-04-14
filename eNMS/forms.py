from eNMS.admin.forms import InstanceForm, UserForm
from eNMS.automation.forms import JobForm
from eNMS.inventory.forms import DeviceForm, LinkForm, PoolForm
from eNMS.scheduling.forms import TaskForm

form_classes = {
    "device": DeviceForm,
    "instance": InstanceForm,
    "link": LinkForm,
    "pool": PoolForm,
    "user": UserForm,
    "service": JobForm,
    "task": TaskForm,
    "workflow": JobForm,
}

form_templates = {
    "device": "base_form",
    "instance": "base_form",
    "link": "base_form",
    "pool": "pool_form",
    "task": "base_form",
}

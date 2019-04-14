from eNMS.admin.forms import InstanceForm, UserForm
from eNMS.automation.forms import JobForm
from eNMS.inventory.forms import DeviceForm, LinkForm, PoolForm
from eNMS.scheduling.forms import TaskForm

type_to_forms = {
    "device": DeviceForm,
    "instance": InstanceForm,
    "link": LinkForm,
    "pool": PoolForm,
    "user": UserForm,
    "service": JobForm,
    "task": TaskForm,
    "workflow": JobForm,
}

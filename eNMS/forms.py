from eNMS.admin.forms import InstanceForm, UserForm
from eNMS.inventory.forms import DeviceForm, LinkForm, PoolForm

type_to_forms = {
    "device": DeviceForm,
    "instance": InstanceForm,
    "link": LinkForm,
    "pool": PoolForm,
    "user": UserForm,
}

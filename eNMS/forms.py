from eNMS.admin.forms import InstanceForm, UserForm
from eNMS.automation.forms import (
    AddJobsForm,
    CompareResultsForm,
    JobForm,
    LogAutomationForm,
)
from eNMS.inventory.forms import (
    CompareConfigurationsForm,
    ConnectionForm,
    DeviceAutomationForm,
    DeviceFilteringForm,
    DeviceForm,
    LinkForm,
    LinkFilteringForm,
    PoolForm,
    PoolObjectsForm,
)
from eNMS.scheduling.forms import TaskForm

form_classes = {
    "add_jobs": AddJobsForm,
    "configuration": CompareConfigurationsForm,
    "configuration_filtering": DeviceFilteringForm,
    "connection": ConnectionForm,
    "device": DeviceForm,
    "device_automation": DeviceAutomationForm,
    "device_filtering": DeviceFilteringForm,
    "instance": InstanceForm,
    "link": LinkForm,
    "link_filtering": LinkFilteringForm,
    "logrule": LogAutomationForm,
    "pool": PoolForm,
    "pool_objects": PoolObjectsForm,
    "results": CompareResultsForm,
    "user": UserForm,
    "service": JobForm,
    "task": TaskForm,
    "workflow": JobForm,
}

form_templates = {
    "configuration_filtering": "filtering_form",
    "device": "base_form",
    "device_filtering": "filtering_form",
    "instance": "base_form",
    "link": "base_form",
    "link_filtering": "filtering_form",
    "task": "base_form",
    "user": "base_form",
}

form_properties = {
    "add_jobs": ("add_jobs",),
    "advanced": ("clear_logs_date", "deletion_types", "import_export_types"),
    "configuration_filtering": ("pools",),
    "device_automation": ("jobs",),
    "device_filtering": ("pools",),
    "link": ("link-source", "link-destination"),
    "link_filtering": ("pools",),
    "logrule": ("jobs",),
    "pool_objects": ("devices", "links"),
    "service": ("devices", "pools"),
    "task": ("start_date", "end_date", "job"),
    "user": ("permissions", "pools"),
    "workflow": ("devices", "pools"),
}

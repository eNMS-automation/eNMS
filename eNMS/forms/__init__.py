from collections import defaultdict
from flask_login import current_user
from wtforms.fields.core import UnboundField

form_properties = defaultdict(dict)


def metaform(*args, **kwargs):
    cls = type(*args, **kwargs)
    for form_type in cls.form_type.kwargs["default"].split(","):
        form_properties[form_type].update(
            {
                field_name: field_types[field.field_class]
                for field_name, field in args[-1].items()
                if isinstance(field, UnboundField) and field.field_class in field_types
            }
        )
    return cls


def form_postprocessing(form):
    data = {**form.to_dict(), **{"creator": current_user.id}}
    for property, field_type in form_properties[form["form_type"]].items():
        if field_type in ("object-list", "multiselect"):
            data[property] = form.getlist(property)
        elif field_type == "boolean":
            data[property] = property in form
    return data


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
    "log_filtering": LogFilteringForm,
    "logrule": LogAutomationForm,
    "pool": PoolForm,
    "pool_objects": PoolObjectsForm,
    "results": CompareResultsForm,
    "service": JobForm,
    "service_filtering": JobFilteringForm,
    "task": TaskForm,
    "user": UserForm,
    "user_filtering": UserFilteringForm,
    "workflow": JobForm,
}

form_templates = {
    "configuration_filtering": "filtering_form",
    "device": "base_form",
    "device_filtering": "filtering_form",
    "instance": "base_form",
    "link": "base_form",
    "link_filtering": "filtering_form",
    "log_filtering": "filtering_form",
    "service_filtering": "filtering_form",
    "task": "base_form",
    "user": "base_form",
    "user_filtering": "filtering_form",
}

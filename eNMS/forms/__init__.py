from collections import defaultdict
from flask_login import current_user
from wtforms.fields.core import UnboundField

from eNMS.forms.fields import field_types
from eNMS.models import property_types

form_actions = {}
form_classes = {}
form_properties = defaultdict(dict)
form_templates = {}


def metaform(*args, **kwargs):
    cls = type(*args, **kwargs)
    form_type = cls.form_type.kwargs["default"]
    form_classes[form_type] = cls
    form_templates[form_type] = getattr(cls, "template", "base")
    form_actions[form_type] = getattr(cls, "action", None)
    properties = {
        field_name: field_types[field.field_class]
        for field_name, field in args[-1].items()
        if isinstance(field, UnboundField) and field.field_class in field_types
    }
    form_properties[form_type].update(properties)
    property_types.update(properties)
    for base in cls.__bases__:
        if not hasattr(base, "form_type"):
            continue
        base_form_type = base.form_type.kwargs["default"]
        if base_form_type == "service":
            cls.service_fields = list(properties)
        form_properties[form_type].update(form_properties[base_form_type])

    return cls


def form_postprocessing(form):
    data = {**form.to_dict(), **{"creator": current_user.id}}
    for property, field_type in form_properties[form.get("form_type")].items():
        if field_type in ("object-list", "multiselect"):
            data[property] = form.getlist(property)
        elif field_type == "boolean":
            data[property] = property in form
    return data


import eNMS.forms.inventory

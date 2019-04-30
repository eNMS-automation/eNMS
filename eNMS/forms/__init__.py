from collections import defaultdict
from flask_login import current_user
from wtforms.fields.core import UnboundField

from eNMS.forms.fields import field_types

form_actions = {}
form_classes = {}
form_properties = defaultdict(dict)
form_templates = {}


def metaform(*args, **kwargs):
    cls = type(*args, **kwargs)
    types = cls.form_type.kwargs["default"]
    form_classes[types] = cls
    form_templates[types] = getattr(cls, "template", types)
    form_actions[types] = getattr(cls, "action", None)
    for form_type in types.split(","):
        form_properties[form_type].update(
            {
                field_name: field_types[field.field_class]
                for field_name, field in args[-1].items()
                if isinstance(field, UnboundField) and field.field_class in field_types
            }
        )
    print(form_properties)
    return cls


def form_postprocessing(form):
    data = {**form.to_dict(), **{"creator": current_user.id}}
    for property, field_type in form_properties[form.get("form_type")].items():
        if field_type in ("object-list", "multiselect"):
            data[property] = form.getlist(property)
        elif field_type == "boolean":
            data[property] = property in form
    return data

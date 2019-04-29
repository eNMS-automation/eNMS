from collections import defaultdict
from flask_login import current_user

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

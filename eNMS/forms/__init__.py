from collections import defaultdict
from flask import request
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms.fields.core import UnboundField
from wtforms.form import FormMeta

from eNMS.forms.fields import field_types, InstanceField, MultipleInstanceField
from eNMS.models import property_types, relationships
from eNMS.properties import field_conversion, property_names


form_actions = {}
form_classes = {}
form_properties = defaultdict(dict)
form_templates = {}


class MetaForm(FormMeta):
    def __new__(cls, name, bases, attrs):
        form: FlaskForm = type.__new__(cls, name, bases, attrs)
        if name == "BaseForm":
            return form
        form_type = form.form_type.kwargs["default"]
        form_classes[form_type] = form
        form_templates[form_type] = getattr(form, "template", "base")
        form_actions[form_type] = getattr(form, "action", None)
        properties = {
            field_name: {
                "type": field_types[field.field_class],
                "model": field.kwargs.pop("model", None),
            }
            for field_name, field in attrs.items()
            if isinstance(field, UnboundField) and field.field_class in field_types
        }
        property_names.update(
            {
                field_name: field.args[0]
                for field_name, field in attrs.items()
                if isinstance(field, UnboundField)
                and field.args
                and isinstance(field.args[0], str)
            }
        )
        form_properties[form_type].update(properties)
        for property, value in properties.items():
            if property not in property_types and value["type"] != "field-list":
                property_types[property] = value["type"]
        for base in form.__bases__:
            if not hasattr(base, "form_type"):
                continue
            base_form_type = base.form_type.kwargs["default"]
            if base_form_type == "service":
                form.service_fields = list(properties)
            if getattr(base, "abstract_service", False):
                form.service_fields.extend(form_properties[base_form_type])
            form_properties[form_type].update(form_properties[base_form_type])
        return form


class BaseForm(FlaskForm, metaclass=MetaForm):
    pass


def form_postprocessing(form, form_data):
    data = {**form_data.to_dict(), **{"user": current_user}}
    if request.files:
        data["file"] = request.files["file"]
    for property, field in form_properties[form_data.get("form_type")].items():
        if field["type"] in ("object-list", "multiselect"):
            data[property] = form_data.getlist(property)
        elif field["type"] == "field-list":
            data[property] = []
            for entry in getattr(form, property).entries:
                properties = entry.data
                properties.pop("csrf_token")
                data[property].append(properties)
        elif field["type"] == "bool":
            data[property] = property in form_data
        elif field["type"] in field_conversion and property in data:
            data[property] = field_conversion[field["type"]](form_data[property])
    return data


def configure_relationships(cls):
    form_type = cls.form_type.kwargs["default"]
    for related_model, relation in relationships[form_type].items():
        field = MultipleInstanceField if relation["list"] else InstanceField
        field_type = "object-list" if relation["list"] else "object"
        form_properties[form_type][related_model] = {"type": field_type}
        setattr(cls, related_model, field())
    return cls

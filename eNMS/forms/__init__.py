from collections import defaultdict
from flask import request
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms.fields.core import UnboundField
from wtforms.form import FormMeta

from eNMS import app
from eNMS.database import db
from eNMS.forms.fields import (
    BooleanField,
    DictField,
    InstanceField,
    IntegerField,
    JsonField,
    MultipleInstanceField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    StringField,
)
from eNMS.models import property_types, relationships

form_actions = {}
form_classes = {}
form_properties = defaultdict(dict)
form_templates = {}


class MetaForm(FormMeta):
    def __new__(cls, name, bases, attrs):
        if name == "BaseForm":
            return type.__new__(cls, name, bases, attrs)
        form_type = attrs["form_type"].kwargs["default"]
        form = type.__new__(cls, name, bases, attrs)
        if not hasattr(form, "custom_properties"):
            form.custom_properties = {}
        form.custom_properties = {
            **form.custom_properties,
            **app.properties["custom"].get(form_type, {}),
        }
        for property, values in form.custom_properties.items():
            if not values.get("form", True):
                continue
            if property in db.private_properties:
                field = PasswordField
            else:
                field = {
                    "boolean": BooleanField,
                    "dict": DictField,
                    "integer": IntegerField,
                    "json": JsonField,
                    "string": StringField,
                    "select": SelectField,
                    "multiselect": SelectMultipleField,
                }[values.get("type", "string")]
            form_kw = {"default": values["default"]} if "default" in values else {}
            if field in (SelectField, SelectMultipleField):
                form_kw["choices"] = values["choices"]
            field = field(values["pretty_name"], **form_kw)
            setattr(form, property, field)
            attrs[property] = field
        form_classes[form_type] = form
        form_templates[form_type] = getattr(form, "template", "base")
        form_actions[form_type] = getattr(form, "action", None)
        properties = {}
        for field_name, field in attrs.items():
            if not isinstance(field, UnboundField):
                continue
            field_type = field.kwargs.pop("type", None)
            if not field_type:
                field_type = field.field_class.type
            properties[field_name] = {
                "type": field_type,
                "model": field.kwargs.pop("model", None),
            }
            if field.args and isinstance(field.args[0], str):
                app.property_names[field_name] = field.args[0]
            if (
                issubclass(field.field_class, PasswordField)
                and field_name not in db.private_properties
            ):
                db.private_properties.append(field_name)
        form_properties[form_type].update(properties)
        for property, value in properties.items():
            if property not in property_types and value["type"] != "field-list":
                property_types[property] = value["type"]
        for base in form.__bases__:
            if not hasattr(base, "form_type"):
                continue
            base_form_type = base.form_type.kwargs["default"]
            form.custom_properties.update(base.custom_properties)
            if base_form_type == "service":
                form.service_fields = [
                    property
                    for property in properties
                    if property not in form.custom_properties
                ]
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
        if field["type"] in ("object-list", "multiselect", "multiselect-string"):
            value = form_data.getlist(property)
            if field["type"] == "multiselect-string":
                value = str(value)
            data[property] = value
        elif field["type"] == "object":
            data[property] = form_data.get(property)
        elif field["type"] == "field-list":
            data[property] = []
            for entry in getattr(form, property).entries:
                properties = entry.data
                properties.pop("csrf_token")
                data[property].append(properties)
        elif field["type"] == "bool":
            data[property] = property in form_data
        elif field["type"] in db.field_conversion and property in data:
            data[property] = db.field_conversion[field["type"]](form_data[property])
    return data


def choices(iterable):
    return [(choice, choice) for choice in iterable]


def configure_relationships(*models):
    def configure_class_relationships(cls):
        form_type = cls.form_type.kwargs["default"]
        for related_model, relation in relationships[form_type].items():
            if related_model not in models:
                continue
            field = MultipleInstanceField if relation["list"] else InstanceField
            field_type = "object-list" if relation["list"] else "object"
            form_properties[form_type][related_model] = {"type": field_type}
            setattr(cls, related_model, field())

    return configure_class_relationships

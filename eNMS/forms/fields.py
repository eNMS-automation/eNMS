from flask_wtf import FlaskForm
from typing import Any
from wtforms import (
    BooleanField,
    FloatField,
    IntegerField,
    SelectField,
    StringField,
    SelectMultipleField,
)

from eNMS.database.functions import choices


class DateField(StringField):
    pass


class DictField(StringField):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["default"] = kwargs.get("default", "{}")
        super().__init__(*args, **kwargs)


class InstanceField(SelectField):
    def __init__(self, model: str, *args: Any, **kwargs: Any) -> None:
        instance_type = kwargs.pop("instance_type")
        super().__init__(*args, **kwargs)
        self.choices = choices(instance_type)


class MultipleInstanceField(SelectMultipleField):
    def __init__(self, model: str, *args: Any, **kwargs: Any) -> None:
        instance_type = kwargs.pop("instance_type")
        super().__init__(*args, **kwargs)
        self.choices = choices(instance_type)

    def pre_validate(self, form: FlaskForm) -> None:
        pass


field_types = {
    BooleanField: "bool",
    DateField: "date",
    DictField: "dict",
    FloatField: "float",
    IntegerField: "integer",
    MultipleInstanceField: "object-list",
    InstanceField: "object",
    SelectField: "list",
    SelectMultipleField: "multiselect",
    StringField: "str",
}

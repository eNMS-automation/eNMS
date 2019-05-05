from wtforms import (
    BooleanField,
    FloatField,
    IntegerField,
    SelectField,
    StringField,
    SelectMultipleField,
)
from typing import Any

from eNMS.database import choices


class DateField(StringField):
    pass


class DictField(StringField):
    pass


class InstanceField(SelectField):
    def __init__(self, model: str, *args: Any, **kwargs: Any) -> None:
        instance_type = kwargs.pop("instance_type")
        super().__init__(*args, **kwargs)
        self.choices = choices(instance_type)


class MultipleInstanceField(SelectMultipleField):
    def __init__(self, model: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.choices = choices(instance_type)

    def pre_validate(self, form):
        pass


field_types = {
    BooleanField: "boolean",
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

from flask_wtf import FlaskForm
from json import loads
from json.decoder import JSONDecodeError
from typing import Any
from wtforms import (
    BooleanField,
    FloatField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SelectMultipleField,
)
from wtforms.validators import ValidationError

from eNMS.database.functions import choices


class DateField(StringField):
    pass


class JsonField(StringField):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def pre_validate(self, form: FlaskForm) -> bool:
        try:
            loads(self.data)
        except JSONDecodeError:
            raise ValidationError("This field contains invalid JSON.")
        return True


class JsonSubstitutionField(JsonField):
    def __call__(self, *args: Any, **kwargs: Any) -> str:
        kwargs["style"] = "background-color: #e8f0f7"
        return super().__call__(*args, **kwargs)


class DictField(StringField):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["default"] = kwargs.get("default", "{}")
        super().__init__(*args, **kwargs)

    def pre_validate(self, form: FlaskForm) -> bool:
        try:
            result = loads(self.data)
        except JSONDecodeError:
            raise ValidationError("Invalid JSON dictionary.")
        if not isinstance(result, dict):
            raise ValidationError("This field only accepts dictionaries.")
        return True


class DictSubstitutionField(DictField):
    def __call__(self, *args: Any, **kwargs: Any) -> str:
        kwargs["style"] = "background-color: #e8f0f7"
        return super().__call__(*args, **kwargs)


class InstanceField(SelectField):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        instance_type = kwargs.pop("instance_type")
        kwargs["coerce"] = int
        super().__init__(*args, **kwargs)
        self.choices = choices(instance_type)


class MultipleInstanceField(SelectMultipleField):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        instance_type = kwargs.pop("instance_type")
        super().__init__(*args, **kwargs)
        self.choices = choices(instance_type)

    def pre_validate(self, form: FlaskForm) -> None:
        pass


class SubstitutionField(StringField):
    def __call__(self, *args: Any, **kwargs: Any) -> str:
        kwargs["style"] = "background-color: #e8f0f7"
        return super().__call__(*args, **kwargs)


class PasswordSubstitutionField(PasswordField):
    def __call__(self, *args: Any, **kwargs: Any) -> str:
        kwargs["style"] = "background-color: #e8f0f7"
        return super().__call__(*args, **kwargs)


class NoValidationSelectField(SelectField):
    def pre_validate(self, form: FlaskForm) -> None:
        pass


class NoValidationSelectMultipleField(SelectMultipleField):
    def pre_validate(self, form: FlaskForm) -> None:
        pass


field_types = {
    BooleanField: "bool",
    DateField: "date",
    DictField: "dict",
    DictSubstitutionField: "dict",
    FloatField: "float",
    InstanceField: "object",
    IntegerField: "integer",
    JsonField: "json",
    JsonSubstitutionField: "json",
    MultipleInstanceField: "object-list",
    NoValidationSelectMultipleField: "multiselect",
    NoValidationSelectField: "list",
    PasswordSubstitutionField: "str",
    SelectField: "list",
    SelectMultipleField: "multiselect",
    StringField: "str",
    SubstitutionField: "str",
}

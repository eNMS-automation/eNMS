from ast import literal_eval
from json import loads
from json.decoder import JSONDecodeError
from wtforms import (
    BooleanField,
    FieldList,
    FloatField,
    IntegerField,
    PasswordField,
    SelectField as WtformsSelectField,
    StringField as WtformsStringField,
    SelectMultipleField,
)
from wtforms.validators import ValidationError

from eNMS import app


class StringField(WtformsStringField):
    type = "str"
    def __init__(self, *args, **kwargs):
        if "type" in kwargs:
            self.type = kwargs.pop("type")
        if kwargs.pop("substitution", False):
            self.color = "E8F0F7"
        elif kwargs.pop("python", False):
            self.color = "FFE8F6"
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if hasattr(self, "color"):
            kwargs["style"] = f"background-color: #{self.color}"
        return super().__call__(*args, **kwargs)


class SelectField(WtformsSelectField):
    type = "list"


class DictField(StringField):
    type = "dict"
    def __init__(self, *args, **kwargs):
        kwargs["default"] = kwargs.get("default", "{}")
        self.json_only = kwargs.pop("json_only", False)
        super().__init__(*args, **kwargs)
        

    def pre_validate(self, form):
        invalid_dict, invalid_json = False, False
        try:
            result = loads(self.data)
        except Exception:
            invalid_json = True
        if self.json_only and invalid_json:
            raise ValidationError("Invalid json syntax.")
        try:
            result = literal_eval(self.data)
        except Exception:
            invalid_dict = True
        if invalid_dict and invalid_json:
            raise ValidationError("Invalid dictionary syntax.")
        if not isinstance(result, dict) and not self.json_only:
            raise ValidationError("This field only accepts dictionaries.")
        if app.contains_set(result):
            raise ValidationError("Sets are not allowed.")
        return True


class InstanceField(SelectField):
    type = "object"
    def __init__(self, *args, **kwargs):
        kwargs["coerce"] = int
        super().__init__(*args, **kwargs)
        self.choices = ()

    def pre_validate(self, form):
        pass


class MultipleInstanceField(SelectMultipleField):
    type = "object-list"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.choices = ()

    def pre_validate(self, form):
        pass


class SubstitutionField(StringField):
    type="str"
    def __call__(self, *args, **kwargs):
        kwargs["style"] = "background-color: #e8f0f7"
        return super().__call__(*args, **kwargs)


class PasswordSubstitutionField(PasswordField):
    type="str"
    def __call__(self, *args, **kwargs):
        kwargs["style"] = "background-color: #e8f0f7"
        return super().__call__(*args, **kwargs)


class NoValidationSelectField(SelectField):
    type = "list"
    def pre_validate(self, form):
        pass


class NoValidationSelectMultipleField(SelectMultipleField):
    type = "multiselect"
    def pre_validate(self, form):
        pass


field_types = {
    BooleanField: "bool",
    FieldList: "field-list",
    FloatField: "float",
    InstanceField: "object",
    IntegerField: "integer",
    MultipleInstanceField: "object-list",
    NoValidationSelectMultipleField: "multiselect",
    NoValidationSelectField: "list",
    PasswordField: "str",
    PasswordSubstitutionField: "str",
    SelectField: "list",
    SelectMultipleField: "multiselect",
    StringField: "str",
    SubstitutionField: "str",
}

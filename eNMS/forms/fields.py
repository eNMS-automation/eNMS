from ast import literal_eval
from json import loads
from json.decoder import JSONDecodeError
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


class DateField(StringField):
    pass


class JsonField(StringField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def pre_validate(self, form):
        try:
            loads(self.data)
        except JSONDecodeError:
            raise ValidationError("This field contains invalid JSON.")
        return True


class JsonSubstitutionField(JsonField):
    def __call__(self, *args, **kwargs):
        kwargs["style"] = "background-color: #e8f0f7"
        return super().__call__(*args, **kwargs)


class DictField(StringField):
    def __init__(self, *args, **kwargs):
        kwargs["default"] = kwargs.get("default", "{}")
        super().__init__(*args, **kwargs)

    def pre_validate(self, form):
        invalid_dict, invalid_json = False, False
        try:
            result = literal_eval(self.data)
        except Exception:
            invalid_dict = True
        try:
            result = loads(self.data)
        except Exception:
            invalid_json = True
        if invalid_dict and invalid_json:
            raise ValidationError("Invalid dictionary syntax.")
        if not isinstance(result, dict):
            raise ValidationError("This field only accepts dictionaries.")
        return True


class DictSubstitutionField(DictField):
    def __call__(self, *args, **kwargs):
        kwargs["style"] = "background-color: #e8f0f7"
        return super().__call__(*args, **kwargs)


class InstanceField(SelectField):
    def __init__(self, *args, **kwargs):
        kwargs["coerce"] = int
        super().__init__(*args, **kwargs)
        self.choices = ()


class MultipleInstanceField(SelectMultipleField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.choices = ()

    def pre_validate(self, form):
        pass


class SubstitutionField(StringField):
    def __call__(self, *args, **kwargs):
        kwargs["style"] = "background-color: #e8f0f7"
        return super().__call__(*args, **kwargs)


class PasswordSubstitutionField(PasswordField):
    def __call__(self, *args, **kwargs):
        kwargs["style"] = "background-color: #e8f0f7"
        return super().__call__(*args, **kwargs)


class NoValidationSelectField(SelectField):
    def pre_validate(self, form):
        pass


class NoValidationSelectMultipleField(SelectMultipleField):
    def pre_validate(self, form):
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

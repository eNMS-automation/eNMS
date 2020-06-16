from ast import literal_eval, parse
from json import loads
from wtforms import (
    BooleanField as WtformsBooleanField,
    Field as WtformsField,
    FieldList as WtformsFieldList,
    FloatField as WtformsFloatField,
    HiddenField as WtformsHiddenField,
    IntegerField as WtformsIntegerField,
    PasswordField as WtformsPasswordField,
    SelectField as WtformsSelectField,
    StringField as WtformsStringField,
    SelectMultipleField as WtformsSelectMultipleField,
)
from wtforms.validators import ValidationError
from wtforms.widgets import html_params
from wtforms.widgets.core import HTMLString

from eNMS import app


class HiddenField(WtformsHiddenField):
    type = "hidden"


class StringField(WtformsStringField):
    type = "str"

    def __init__(self, *args, **kwargs):
        self.python = kwargs.pop("python", False)
        if "type" in kwargs:
            self.type = kwargs.pop("type")
        if kwargs.pop("substitution", False):
            self.color = "E8F0F7"
        elif self.python:
            self.color = "FFE8F6"
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if hasattr(self, "color"):
            kwargs["style"] = f"background-color: #{self.color}"
        return super().__call__(*args, **kwargs)

    def pre_validate(self, form):
        if self.python:
            try:
                parse(self.data)
            except Exception as exc:
                raise ValidationError(f"Wrong python expression ({exc}).")
        return True


class BooleanField(WtformsBooleanField):
    type = "bool"


class IntegerField(WtformsIntegerField):
    type = "integer"


class FloatField(WtformsFloatField):
    type = "float"


class SelectField(WtformsSelectField):
    type = "list"

    def __init__(self, *args, **kwargs):
        if not kwargs.pop("validation", True):
            self.pre_validate = lambda *a, **kw: None
        super().__init__(*args, **kwargs)


class SelectMultipleField(WtformsSelectMultipleField):
    type = "multiselect"


class SelectMultipleStringField(SelectMultipleField):
    type = "multiselect-string"


class FieldList(WtformsFieldList):
    type = "field-list"


class PasswordField(WtformsPasswordField):
    type = "str"

    def __init__(self, *args, **kwargs):
        self.color = kwargs.pop("substitution", False)
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if self.color:
            kwargs["style"] = "background-color: #e8f0f7"
        return super().__call__(*args, **kwargs)


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


class JsonField(WtformsField):
    type = "json"

    def __init__(self, *args, **kwargs):
        self.name = kwargs.get("_name")
        super().__init__(*args, **kwargs)

    def __call__(self, **kwargs):
        html_kwargs = {"id": kwargs["id"], "class_": "add-id", "name": self.name}
        return HTMLString(f"<input {html_params(**html_kwargs)} hidden><div></div>")


class InstanceField(SelectField):
    type = "object"

    def __init__(self, *args, **kwargs):
        kwargs["coerce"] = int
        super().__init__(*args, **kwargs)
        self.choices = ()

    def pre_validate(self, form):
        pass


class MultipleInstanceField(WtformsSelectMultipleField):
    type = "object-list"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.choices = ()

    def pre_validate(self, form):
        pass

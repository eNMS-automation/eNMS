from ast import literal_eval, parse
from json import loads
from markupsafe import Markup
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


from eNMS.database import db
from eNMS.variables import vs


class MetaField(type):
    def __new__(cls, name, bases, attrs):
        field_class = type.__new__(cls, name, bases, attrs)
        vs.field_class[name] = field_class
        return field_class


class FieldMixin(metaclass=MetaField):
    def __init__(self, *args, **kwargs):
        if "help" in kwargs:
            kwargs.setdefault("render_kw", {})["help"] = kwargs.pop("help")
        kwargs.pop("dont_duplicate", None)
        super().__init__(*args, **kwargs)


class HiddenField(FieldMixin, WtformsHiddenField):
    type = "hidden"


class StringField(FieldMixin, WtformsStringField):
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

    def pre_validate(self, _):
        if self.python:
            try:
                parse(self.data)
            except Exception as exc:
                raise ValidationError(f"Wrong python expression ({exc}).")
        return True


class BooleanField(FieldMixin, WtformsBooleanField):
    type = "bool"


class IntegerField(FieldMixin, WtformsIntegerField):
    type = "integer"


class FloatField(FieldMixin, WtformsFloatField):
    type = "float"


class SelectField(FieldMixin, WtformsSelectField):
    type = "list"


class SelectMultipleField(FieldMixin, WtformsSelectMultipleField):
    type = "multiselect"


class FieldList(FieldMixin, WtformsFieldList):
    type = "field-list"


class PasswordField(FieldMixin, WtformsPasswordField):
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

    def contains_set(self, input):
        if isinstance(input, set):
            return True
        elif isinstance(input, list):
            return any(self.contains_set(item) for item in input)
        elif isinstance(input, dict):
            return any(self.contains_set(item) for item in input.values())
        else:
            return False

    def pre_validate(self, _):
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
        if self.contains_set(result):
            raise ValidationError("Sets are not allowed.")
        return True


class JsonField(FieldMixin, WtformsField):
    type = "json"

    def __init__(self, *args, **kwargs):
        self.name = kwargs.get("_name")
        super().__init__(*args, **kwargs)

    def __call__(self, **kwargs):
        class_ = "add-id collapsed" if "collapsed" in kwargs["class"] else "add-id"
        html_kwargs = {"id": kwargs["id"], "class_": class_, "name": self.name}
        return Markup(f"<input {html_params(**html_kwargs)} hidden><div></div>")


class InstanceField(SelectField):
    type = "object"

    def __init__(self, *args, **kwargs):
        kwargs["coerce"] = int
        self.constraints = kwargs.pop("constraints", None)
        self.model = kwargs.pop("model", None)
        super().__init__(*args, **kwargs)
        self.choices = ()

    def pre_validate(self, _):
        pass


class MultipleInstanceField(FieldMixin, WtformsSelectMultipleField):
    type = "object-list"

    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop("model")
        super().__init__(*args, **kwargs)
        self.choices = ()

    def pre_validate(self, _):
        not_found = [
            name
            for name in self.data
            if not db.fetch(self.model, rbac=None, name=name, allow_none=True)
        ]
        if len(set(self.data)) != len(self.data):
            raise ValidationError(f"Duplicated {self.model}s selected.")
        if not_found:
            error = f"Couldn't find the following {self.model}s: {', '.join(not_found)}"
            raise ValidationError(error)
        return True

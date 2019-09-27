from wtforms import BooleanField, FloatField, HiddenField, IntegerField, SelectField
from wtforms.widgets import TextArea

from eNMS import app
from eNMS.forms import BaseForm
from eNMS.forms.fields import DictField, DictSubstitutionField, SubstitutionField


class StringValidationForm(BaseForm):
    form_type = HiddenField(default="string_service_validation")
    abstract_service = True
    content_match = SubstitutionField(
        "Content Match", widget=TextArea(), render_kw={"rows": 8}
    )
    content_match_regex = BooleanField("Match content with Regular Expression")
    negative_logic = BooleanField("Negative logic")
    delete_spaces_before_matching = BooleanField("Delete Spaces before Matching")
    group = {
        "commands": [
            "content_match",
            "content_match_regex",
            "negative_logic",
            "delete_spaces_before_matching",
        ],
        "default": "expanded",
    }


class DictValidationForm(BaseForm):
    form_type = HiddenField(default="dict_service_validation")
    abstract_service = True
    validation_method = SelectField(
        "Validation Method",
        choices=(
            ("dict_included", "Validation by dictionary inclusion"),
            ("dict_equal", "Validation by dictionary equality"),
        ),
    )
    dict_match = DictSubstitutionField("Dictionary to Match Against")
    negative_logic = BooleanField("Negative logic")
    group = {
        "commands": ["validation_method", "dict_match", "negative_logic"],
        "default": "expanded",
    }


class ValidationForm(BaseForm):
    form_type = HiddenField(default="service_validation")
    abstract_service = True
    conversion_method = SelectField(
        choices=(
            ("none", "No conversion"),
            ("text", "Text"),
            ("json", "Json dictionary"),
            ("xml", "XML dictionary"),
        )
    )
    validation_method = SelectField(
        "Validation Method",
        choices=(
            ("text", "Validation by text match"),
            ("dict_included", "Validation by dictionary inclusion"),
            ("dict_equal", "Validation by dictionary equality"),
        ),
    )
    content_match = SubstitutionField(
        "Content Match", widget=TextArea(), render_kw={"rows": 8}
    )
    content_match_regex = BooleanField("Match content with Regular Expression")
    dict_match = DictSubstitutionField("Dictionary to Match Against")
    negative_logic = BooleanField("Negative logic")
    delete_spaces_before_matching = BooleanField("Delete Spaces before Matching")
    group = {
        "commands": [
            "conversion_method",
            "validation_method",
            "content_match",
            "content_match_regex",
            "dict_match",
            "negative_logic",
            "delete_spaces_before_matching",
        ],
        "default": "expanded",
    }

    def validate(self):
        valid_form = super().validate()
        conversion_validation_mismatch = (
            self.conversion_method.data == "text"
            and "dict" in self.validation_method.data
            or self.conversion_method.data in ("xml", "json")
            and "dict" not in self.validation_method.data
        )
        if conversion_validation_mismatch:
            self.conversion_method.errors.append(
                f"The conversion method is set to '{self.conversion_method.data}'"
                f" and the validation method to '{self.validation_method.data}' :"
                " these do not match."
            )
        return valid_form and not conversion_validation_mismatch


class NetmikoForm(BaseForm):
    form_type = HiddenField(default="netmiko")
    abstract_service = True
    driver = SelectField(choices=app.NETMIKO_DRIVERS)
    use_device_driver = BooleanField(default=True)
    privileged_mode = BooleanField("Privileged mode (run in enable mode or as root)")
    fast_cli = BooleanField()
    timeout = IntegerField(default=10)
    delay_factor = FloatField(default=1.0)
    global_delay_factor = FloatField(default=1.0)
    group = {
        "commands": [
            "driver",
            "use_device_driver",
            "privileged_mode",
            "fast_cli",
            "timeout",
            "delay_factor",
            "global_delay_factor",
        ],
        "default": "expanded",
    }


class NapalmForm(BaseForm):
    form_type = HiddenField(default="napalm")
    abstract_service = True
    driver = SelectField(choices=app.NAPALM_DRIVERS)
    use_device_driver = BooleanField(default=True)
    optional_args = DictField()
    group = {
        "commands": ["driver", "use_device_driver", "optional_args"],
        "default": "expanded",
    }


class ConnectionForm(BaseForm):
    credentials = SelectField(
        "Credentials",
        choices=(
            ("device", "Device Credentials"),
            ("user", "User Credentials"),
            ("custom", "Custom Credentials"),
        ),
    )
    custom_username = SubstitutionField("Custom Username")
    custom_password = PasswordSubstitutionField("Custom Password")
    start_new_connection = BooleanField("Start New Connection")
    close_connection = BooleanField("Close Connection")
    group = {
        "commands": [
            "credentials",
            "custom_username",
            "custom_password",
            "start_new_connection",
            "close_connection",
        ],
        "default": "expanded",
    }

from wtforms import (
    BooleanField,
    FloatField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
)
from wtforms.widgets import TextArea

from eNMS.controller import controller
from eNMS.forms import BaseForm
from eNMS.forms.fields import DictField


class StringValidationForm(BaseForm):
    form_type = HiddenField(default="string_service_validation")
    abstract_service = True
    content_match = StringField(
        "Content Match", widget=TextArea(), render_kw={"rows": 8}
    )
    content_match_regex = BooleanField("Match content with Regular Expression")
    negative_logic = BooleanField("Negative logic")
    delete_spaces_before_matching = BooleanField("Delete Spaces before Matching")
    group = [
        "content_match",
        "content_match_regex",
        "negative_logic",
        "delete_spaces_before_matching",
    ]


class DictValidationForm(BaseForm):
    form_type = HiddenField(default="dict_service_validation")
    abstract_service = True
    validation_method = SelectField(
        "Validation Method",
        choices=(
            ("dict_equal", "Validation by dictionary equality"),
            ("dict_included", "Validation by dictionary inclusion"),
        ),
    )
    dict_match = DictField("Dictionary to Match Against")
    negative_logic = BooleanField("Negative logic")
    group = ["validation_method", "dict_match", "negative_logic"]


class ValidationForm(BaseForm):
    form_type = HiddenField(default="service_validation")
    abstract_service = True
    validation_method = SelectField(
        "Validation Method",
        choices=(
            ("text", "Validation by text match"),
            ("dict_equal", "Validation by dictionary equality"),
            ("dict_included", "Validation by dictionary inclusion"),
        ),
    )
    content_match = StringField(
        "Content Match", widget=TextArea(), render_kw={"rows": 8}
    )
    content_match_regex = BooleanField("Match content with Regular Expression")
    dict_match = DictField("Dictionary to Match Against")
    negative_logic = BooleanField("Negative logic")
    delete_spaces_before_matching = BooleanField("Delete Spaces before Matching")
    group = [
        "validation_method",
        "content_match",
        "content_match_regex",
        "dict_match",
        "negative_logic",
        "delete_spaces_before_matching",
    ]


class NetmikoForm(BaseForm):
    form_type = HiddenField(default="netmiko")
    abstract_service = True
    driver = SelectField(choices=controller.NETMIKO_DRIVERS)
    use_device_driver = BooleanField(default=True)
    privileged_mode = BooleanField("Privileged mode (run in enable mode or as root)")
    fast_cli = BooleanField()
    timeout = IntegerField(default=10)
    delay_factor = FloatField(default=1.0)
    global_delay_factor = FloatField(default=1.0)
    group = [
        "driver",
        "use_device_driver",
        "privileged_mode",
        "fast_cli",
        "timeout",
        "delay_factor",
        "global_delay_factor",
    ]


class NapalmForm(BaseForm):
    form_type = HiddenField(default="napalm")
    abstract_service = True
    driver = SelectField(choices=controller.NAPALM_DRIVERS)
    use_device_driver = BooleanField(default=True)
    optional_args = DictField()
    group = ["driver", "use_device_driver", "optional_args"]

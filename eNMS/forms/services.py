from wtforms import BooleanField, HiddenField, SelectField, StringField
from wtforms.widgets import TextArea

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

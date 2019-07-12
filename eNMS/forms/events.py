from wtforms import BooleanField, HiddenField, IntegerField, SelectField, StringField
from wtforms.widgets import TextArea

from eNMS.forms import BaseForm, configure_relationships
from eNMS.forms.fields import DateField, DictField, MultipleInstanceField


def configure_form(cls: BaseForm) -> BaseForm:
    cls.properties = ("log_source", "log_content")
    for property in ("log_source", "log_content"):
        setattr(cls, property, StringField(property))
        setattr(cls, property + "_regex", BooleanField("Regex"))
    return cls


@configure_form
class EventForm(BaseForm):
    template = "event"
    form_type = HiddenField(default="event")
    id = HiddenField()
    name = StringField("Name")
    jobs = MultipleInstanceField("Jobs", instance_type="Job")


@configure_relationships
class TaskForm(BaseForm):
    template = "object"
    form_type = HiddenField(default="task")
    id = HiddenField()
    is_active = BooleanField("Is Active")
    name = StringField("Name")
    description = StringField("Description")
    start_date = DateField("Start Date")
    end_date = DateField("End Date")
    frequency = IntegerField("Frequency", default=0)
    frequency_unit = SelectField(
        "Frequency Unit",
        choices=(
            ("seconds", "Seconds"),
            ("minutes", "Minutes"),
            ("hours", "Hours"),
            ("days", "Days"),
        ),
    )
    crontab_expression = StringField("Crontab Expression")
    scheduling_mode = SelectField(
        "Scheduling Mode",
        choices=(("standard", "Standard Scheduling"), ("cron", "Crontab Scheduling")),
    )
    payload = DictField("Payload")


class ChangelogForm(BaseForm):
    template = "object"
    form_type = HiddenField(default="changelog")
    id = HiddenField()
    severity = SelectField(
        "Severity",
        choices=(
            ("debug", "Debug"),
            ("info", "Info"),
            ("warning", "Warning"),
            ("error", "Error"),
            ("critical", "Critical"),
        ),
    )
    content = StringField(widget=TextArea(), render_kw={"rows": 8})

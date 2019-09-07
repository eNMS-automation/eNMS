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
    scheduling_mode = SelectField(
        "Scheduling Mode",
        choices=(("cron", "Crontab Scheduling"), ("standard", "Standard Scheduling")),
    )
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
    payload = DictField("Payload")

    def validate(self) -> bool:
        valid_form = super().validate()
        no_start_date = (
            self.is_active.data
            and self.scheduling_mode.data == "standard"
            and not self.start_date.data
        )
        if no_start_date:
            self.start_date.errors.append("A start date must be set.")
        no_cron_expression = (
            self.is_active.data
            and self.scheduling_mode.data == "cron"
            and not self.crontab_expression.data
        )
        if no_cron_expression:
            self.crontab_expression.errors.append("A crontab expression must be set.")
        return valid_form and not no_start_date and not no_cron_expression


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

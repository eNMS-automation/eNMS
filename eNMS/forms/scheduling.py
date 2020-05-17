from wtforms.validators import InputRequired

from eNMS.forms import BaseForm, configure_relationships
from eNMS.forms.fields import (
    BooleanField,
    DictField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
)


def configure_form(cls):
    cls.properties = ("log_source", "log_content")
    for property in ("log_source", "log_content"):
        setattr(cls, property, StringField(property))
        setattr(cls, property + "_regex", BooleanField("Regex"))
    return cls


@configure_relationships("service")
@configure_form
class EventForm(BaseForm):
    template = "event"
    form_type = HiddenField(default="event")
    id = HiddenField()
    name = StringField("Name", [InputRequired()])


@configure_relationships("devices", "pools", "service")
class TaskForm(BaseForm):
    template = "object"
    form_type = HiddenField(default="task")
    id = HiddenField()
    scheduling_mode = SelectField(
        "Scheduling Mode",
        choices=(("cron", "Crontab Scheduling"), ("standard", "Standard Scheduling")),
    )
    name = StringField("Name", [InputRequired()])
    description = StringField("Description")
    start_date = StringField("Start Date", type="date")
    end_date = StringField("End Date", type="date")
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
    initial_payload = DictField("Payload")

    def validate(self):
        valid_form = super().validate()
        no_date = self.scheduling_mode.data == "standard" and not self.start_date.data
        if no_date:
            self.start_date.errors.append("A start date must be set.")
        no_cron_expression = (
            self.scheduling_mode.data == "cron" and not self.crontab_expression.data
        )
        if no_cron_expression:
            self.crontab_expression.errors.append("A crontab expression must be set.")
        no_service = not self.service.data
        if no_service:
            self.service.errors.append("No service set.")
        return valid_form and not any([no_date, no_cron_expression, no_service])

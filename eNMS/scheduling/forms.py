from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, IntegerField, SelectField, StringField

from eNMS.models.base_models import ObjectField


class TaskForm(FlaskForm):
    id = HiddenField()
    boolean_fields = HiddenField(default="is_active")
    is_active = BooleanField()
    name = StringField()
    description = StringField()
    start_date = StringField()
    end_date = StringField()
    frequency = IntegerField()
    frequency_unit = SelectField(
        choices=(
            ("seconds", "Seconds"),
            ("minutes", "Minutes"),
            ("hours", "Hours"),
            ("days", "Days"),
        )
    )
    crontab_expression = StringField()
    job = ObjectField("Job")
    scheduling_mode = SelectField(
        choices=(("standard", "Standard Scheduling"), ("cron", "Crontab Scheduling"))
    )

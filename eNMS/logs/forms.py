from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, StringField

from eNMS.base.models import MultipleObjectField


def configure_form(cls):
    cls.properties = ('source_ip', 'content')
    for property in ('source_ip', 'content'):
        setattr(cls, property, StringField(property))
        setattr(cls, property + '_regex', BooleanField('Regex'))
    return cls


@configure_form
class LogAutomationForm(FlaskForm):
    id = HiddenField()
    list_fields = HiddenField(default='jobs')
    name = StringField()
    jobs = MultipleObjectField('Job')

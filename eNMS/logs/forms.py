from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, StringField

from eNMS.base.models import MultipleObjectField


def configure_form(cls):
    cls.properties = ('source', 'content')
    for property in ('source', 'content'):
        setattr(cls, property, StringField(property))
        setattr(cls, property + 'regex', BooleanField('Regex'))
    return cls


@configure_form
class LogFilteringForm(FlaskForm):
    pass


class LogAutomationForm(LogFilteringForm):
    id = HiddenField()
    list_fields = HiddenField(default='jobs')
    name = StringField()
    jobs = ObjectMultipleField('Job')

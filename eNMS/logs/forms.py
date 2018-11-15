from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, SelectMultipleField, StringField


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
    name = StringField()
    jobs = SelectMultipleField('Job')

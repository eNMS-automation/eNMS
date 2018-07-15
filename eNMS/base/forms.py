from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectMultipleField, TextField


def configure_form(cls):
    cls.properties = ('source', 'content')
    for property in ('source', 'content'):
        setattr(cls, property, TextField(property))
        setattr(cls, property + 'regex', BooleanField('Regex'))
    return cls


@configure_form
class LogFilteringForm(FlaskForm):
    pass


class LogAutomationForm(LogFilteringForm):
    name = TextField('Name')
    tasks = SelectMultipleField('Tasks', choices=())

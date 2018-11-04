from wtforms import BooleanField, HiddenField, SelectMultipleField, TextField

from eNMS.base.models import BaseForm


def configure_form(cls):
    cls.properties = ('source', 'content')
    for property in ('source', 'content'):
        setattr(cls, property, TextField(property))
        setattr(cls, property + 'regex', BooleanField('Regex'))
    return cls


@configure_form
class LogFilteringForm(BaseForm):
    pass


class LogAutomationForm(LogFilteringForm):
    id = HiddenField()
    name = TextField()
    jobs = SelectMultipleField()

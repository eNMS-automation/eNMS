from collections import OrderedDict
from flask_wtf import FlaskForm
from wtforms import BooleanField, TextField, SelectField
from wtforms.validators import optional

class SchedulingForm(FlaskForm):

    name = TextField('Name')
    scheduled_date = TextField('Datetime')
    script = SelectField('', choices=())
    frequency = TextField('Frequency')

## Compare getters history

class CompareForm(FlaskForm):
    first_node = SelectField('', [optional()], choices=())
    second_node = SelectField('', [optional()], choices=())
    first_version = SelectField('', [optional()], choices=())
    second_version = SelectField('', [optional()], choices=())
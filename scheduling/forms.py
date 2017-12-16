from collections import OrderedDict
from flask_wtf import FlaskForm
from wtforms import TextField, SelectField
from wtforms.validators import optional

class SchedulingForm(FlaskForm):

    name = TextField('Name')
    
    scheduled_date = TextField('Datetime')
    
    frequency_choices = OrderedDict([
    ('Once', None),
    ('Every hour', 60*60),
    ('Once a day', 60*60*24),
    ('Once a week', 60*60*24*7),
    ('Once a month', 60*60*24*30),
    ])
    
    frequency_intervals = [(option, option) for option in frequency_choices]
    frequency = SelectField('', [optional()], choices=frequency_intervals)

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import TextField, SelectField, TextAreaField, FileField
from wtforms.validators import optional

## Script creation

class ScriptCreationForm(FlaskForm):
    name = TextField('Name')
    type_choices = (
        ('simple', 'Simple'),
        ('j2_template', 'Jinja2 template'),
        ('per_device_j2', 'Per-device Jinja2 template')
        )
    type = SelectField('', choices=type_choices)
    text = TextAreaField('')
    file = FileField('', validators=[FileAllowed(['yaml'], 'YAML only')])

## Compare getters history

class CompareForm(FlaskForm):
    first_node = SelectField('', choices=())
    second_node = SelectField('', choices=())
    first_version = SelectField('', choices=())
    second_version = SelectField('', choices=())
from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField

## Compare getters history


class CompareForm(FlaskForm):
    first_version = SelectField('', choices=())
    second_version = SelectField('', choices=())
    first_node = SelectField('', choices=())
    second_node = SelectField('', choices=())
    first_script = SelectField('', choices=())
    second_script = SelectField('', choices=())
    unified_diff = TextAreaField('')
    ndiff = TextAreaField('')

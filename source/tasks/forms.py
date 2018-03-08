from flask_wtf import FlaskForm
from wtforms import SelectField

## Compare getters history


class CompareForm(FlaskForm):
    first_node = SelectField('', choices=())
    second_node = SelectField('', choices=())
    first_version = SelectField('', choices=())
    second_version = SelectField('', choices=())

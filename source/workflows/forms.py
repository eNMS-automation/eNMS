from flask_wtf import FlaskForm
from wtforms import SelectField, TextField


class WorkflowCreationForm(FlaskForm):
    name = TextField('Name')
    scripts = SelectField('', choices=())

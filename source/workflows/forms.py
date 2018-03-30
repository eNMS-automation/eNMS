from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, TextField


class AddScriptForm(FlaskForm):
    scripts = SelectMultipleField('', choices=())


class WorkflowCreationForm(FlaskForm):
    name = TextField('Name')
    description = TextField('Description')

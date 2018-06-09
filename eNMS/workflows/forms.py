from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField, TextField


class WorkflowEditorForm(FlaskForm):
    workflow = SelectField('Workflow', choices=())


class WorkflowCreationForm(FlaskForm):
    name = TextField('Name')
    description = TextField('Description')
    type = TextField('Type')

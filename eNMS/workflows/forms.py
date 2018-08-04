from flask_wtf import FlaskForm
from wtforms import SelectField, TextField


class AddExistingTaskForm(FlaskForm):
    task = SelectField('Workflow', choices=())


class WorkflowCreationForm(FlaskForm):
    name = TextField('Name')
    description = TextField('Description')


class WorkflowEditorForm(FlaskForm):
    workflow = SelectField('Workflow', choices=())

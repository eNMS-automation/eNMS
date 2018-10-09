from flask_wtf import FlaskForm
from wtforms import SelectField, TextField


class AddJobForm(FlaskForm):
    job = SelectField()


class WorkflowCreationForm(FlaskForm):
    name = TextField()
    description = TextField()
    vendor = TextField()
    operating_system = TextField()


class WorkflowEditorForm(FlaskForm):
    workflow = SelectField()

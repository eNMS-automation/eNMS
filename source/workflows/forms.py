from flask_wtf import FlaskForm
from wtforms import SelectMultipleField


class AddScriptForm(FlaskForm):
    scripts = SelectMultipleField('', choices=())

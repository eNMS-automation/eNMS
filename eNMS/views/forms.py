from flask_wtf import FlaskForm
from wtforms import IntegerField, TextField


class GoogleEarthForm(FlaskForm):
    name = TextField()
    label_size = IntegerField(default=1)
    line_width = IntegerField(default=2)

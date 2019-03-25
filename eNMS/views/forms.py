from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField

from eNMS.base.models import ObjectField


class ViewForm(FlaskForm):
    pools = ObjectField("Pool")

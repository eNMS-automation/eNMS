from flask_wtf import FlaskForm

from eNMS.models import ObjectField


class ViewForm(FlaskForm):
    pools = ObjectField("Pool")

from flask_wtf import FlaskForm

from eNMS.base.models import ObjectField


class ViewForm(FlaskForm):
    pools = ObjectField("Pool")

from flask_wtf import FlaskForm
from wtforms import HiddenField

from eNMS.forms import metaform


class InstanceDeletionForm(FlaskForm, metaclass=metaform):
    template = "instance_deletion"
    form_type = HiddenField(default="instance_deletion")

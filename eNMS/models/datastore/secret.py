from sqlalchemy import ForeignKey, Integer
from wtforms.widgets import TextArea

from eNMS.database import db
from eNMS.fields import HiddenField, InstanceField, PasswordField
from eNMS.forms import DataForm
from eNMS.models.administration import Data


class Secret(Data):
    __tablename__ = "secret"
    pretty_name = "Secret"
    __mapper_args__ = {"polymorphic_identity": "secret"}
    id = db.Column(Integer, ForeignKey("data.id"), primary_key=True)
    secret_value = db.Column(db.LargeString)


class SecretForm(DataForm):
    form_type = HiddenField(default="secret")
    store = InstanceField("Store", model="store", constraints={"data_type": "secret"})
    secret_value = PasswordField("Value", widget=TextArea(), render_kw={"rows": 6})
    properties = ["secret_value"]

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.types import JSON

from eNMS.database import db
from eNMS.fields import HiddenField, JsonField, InstanceField
from eNMS.forms import DataForm
from eNMS.models.administration import Data


class JSON(Data):
    __tablename__ = "json"
    pretty_name = "JSON"
    __mapper_args__ = {"polymorphic_identity": "json"}
    id = db.Column(Integer, ForeignKey("data.id"), primary_key=True)
    value = db.Column(JSON, default={})


class JSONForm(DataForm):
    form_type = HiddenField(default="json")
    store = InstanceField("Store", model="store", constraints={"data_type": "json"})
    value = JsonField(collapse=False, div_properties="style='height: 400px'")
    properties = ["value"]

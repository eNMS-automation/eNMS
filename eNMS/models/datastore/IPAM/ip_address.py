from sqlalchemy import ForeignKey, Integer

from eNMS.database import db
from eNMS.fields import HiddenField, InstanceField, SelectField, StringField
from eNMS.forms import DataForm
from eNMS.models.administration import Data


class IPAddress(Data):
    __tablename__ = "ip_address"
    pretty_name = "IP Address"
    __mapper_args__ = {"polymorphic_identity": "ip_address"}
    id = db.Column(Integer, ForeignKey("data.id"), primary_key=True)
    address = db.Column(db.TinyString)
    role = db.Column(db.TinyString)
    vrf_instance = db.Column(db.SmallString)


class IPAdressForm(DataForm):
    form_type = HiddenField(default="ip_address")
    store = InstanceField(
        "Store", model="store", constraints={"data_type": "ip_address"}
    )
    address = StringField()
    role = SelectField(
        "Role",
        choices=(
            ("loopback", "Loopback"),
            ("secondary", "Secondary"),
            ("anycast", "Anycast"),
        ),
    )
    vrf_instance = StringField("VRF Instance")
    properties = ["address", "role", "vrf_instance"]

from sqlalchemy import ForeignKey, Integer

from eNMS.database import db
from eNMS.forms import LinkForm
from eNMS.fields import HiddenField, SelectField, StringField
from eNMS.models.inventory import Link


class EthernetLink(Link):

    __tablename__ = "ethernet_link"
    __mapper_args__ = {"polymorphic_identity": "ethernet_link"}
    pretty_name = "Ethernet Link"
    id = db.Column(Integer, ForeignKey("link.id"), primary_key=True)
    speed = db.Column(db.SmallString)
    standard = db.Column(db.SmallString)


class RouterForm(LinkForm):
    form_type = HiddenField(default="router")
    speed = StringField("Serial Number", default=22)
    standard = SelectField(
        "Standard",	10BASE5, 10BASE2, 10BASE-T, 100BASE-TX, 1000BASE-T, 10GBASE-T
        choices=(
            ("10BASE2", "10BASE2"),
            ("10BASE5", "10BASE5"),
            ("10BASE-T", "10BASE-T"),
            ("1000BASE-T", "1000BASE-T"),
            ("10GBASE-T", "10GBASE-T")
        ),
    )

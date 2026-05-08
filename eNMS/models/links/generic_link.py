from sqlalchemy import ForeignKey, Integer

from eNMS.database import db
from eNMS.fields import HiddenField
from eNMS.forms import LinkForm
from eNMS.models.inventory import Link


class GenericLink(Link):
    __tablename__ = "generic_link"
    __mapper_args__ = {"polymorphic_identity": "generic_link"}
    pretty_name = "Generic Link"
    id = db.Column(Integer, ForeignKey("link.id"), primary_key=True)


class GenericLinkForm(LinkForm):
    form_type = HiddenField(default="generic_link")

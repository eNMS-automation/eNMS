from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import relationship
from wtforms.widgets import TextArea

from eNMS.database import db
from eNMS.forms import BaseForm
from eNMS.fields import (
    HiddenField,
    MultipleInstanceField,
    StringField,
)
from eNMS.models.inventory import Node


class Site(Node):

    __tablename__ = class_type = "site"
    __mapper_args__ = {"polymorphic_identity": "site"}
    pretty_name = "Site"
    parent_type = "node"
    icon = db.Column(db.TinyString, default="site")
    id = db.Column(Integer, ForeignKey(Node.id), primary_key=True)
    labels = db.Column(db.Dict, info={"log_change": False})
    nodes = relationship("Node", secondary=db.node_site_table, back_populates="sites")
    links = relationship("Link", secondary=db.link_site_table, back_populates="sites")
    pools = relationship("Pool", secondary=db.pool_site_table, back_populates="sites")


class SiteForm(BaseForm):
    action = "eNMS.base.processData"
    form_type = HiddenField(default="site")
    id = HiddenField()
    name = StringField("Name")
    longitude = StringField("Longitude", default=0.0)
    latitude = StringField("Latitude", default=0.0)
    sites = MultipleInstanceField("Sites", model="site")
    description = StringField(widget=TextArea(), render_kw={"rows": 6})

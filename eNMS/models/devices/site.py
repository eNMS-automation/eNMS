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
    category = db.Column(db.SmallString)
    icon = db.Column(db.TinyString, default="site")
    id = db.Column(Integer, ForeignKey(Node.id), primary_key=True)
    labels = db.Column(db.Dict, info={"log_change": False})
    nodes = relationship("Node", secondary=db.node_site_table, back_populates="sites")
    links = relationship("Link", secondary=db.link_site_table, back_populates="sites")
    pools = relationship("Pool", secondary=db.pool_site_table, back_populates="sites")

    def duplicate(self, clone=None):
        for property in ("labels", "nodes", "links"):
            setattr(clone, property, getattr(self, property))
        for node in self.nodes:
            node.positions[clone.name] = node.positions.get(self.name, (0, 0))
        db.session.commit()
        return clone

    def update(self, **kwargs):
        old_name = self.name
        super().update(**kwargs)
        if self.name == old_name:
            return
        for node in self.nodes:
            if old_name not in node.positions:
                continue
            node.positions[self.name] = node.positions[old_name]


class SiteForm(BaseForm):
    action = "eNMS.base.processData"
    form_type = HiddenField(default="site")
    id = HiddenField()
    name = StringField("Name")
    longitude = StringField("Longitude", default=0.0)
    latitude = StringField("Latitude", default=0.0)
    sites = MultipleInstanceField("Sites", model="site")
    description = StringField(widget=TextArea(), render_kw={"rows": 6})

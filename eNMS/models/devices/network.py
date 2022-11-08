from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import relationship
from wtforms.widgets import TextArea

from eNMS.database import db, vs
from eNMS.forms import BaseForm
from eNMS.fields import (
    HiddenField,
    MultipleInstanceField,
    SelectField,
    StringField,
)
from eNMS.models.inventory import Node


class Network(Node):

    __tablename__ = class_type = "network"
    __mapper_args__ = {"polymorphic_identity": "network"}
    pretty_name = "Network"
    parent_type = "node"
    category = db.Column(db.SmallString)
    icon = db.Column(db.TinyString, default="network")
    id = db.Column(Integer, ForeignKey(Node.id), primary_key=True)
    path = db.Column(db.TinyString)
    labels = db.Column(db.Dict, info={"log_change": False})
    nodes = relationship(
        "Node", secondary=db.node_network_table, back_populates="networks"
    )
    links = relationship(
        "Link", secondary=db.link_network_table, back_populates="networks"
    )

    def duplicate(self, clone=None):
        for property in ("labels", "nodes", "links"):
            setattr(clone, property, getattr(self, property))
        for node in self.nodes:
            node.positions[clone.name] = node.positions.get(self.name, (0, 0))
        db.session.commit()
        return clone

    def post_update(self):
        if len(self.networks) == 1:
            self.path = f"{self.networks[0].path}>{self.id}"
        else:
            self.path = str(self.id)
        return self.get_properties()

    def update(self, **kwargs):
        old_name = self.name
        super().update(**kwargs)
        if self.name == old_name:
            return
        for node in self.nodes:
            if old_name not in node.positions:
                continue
            node.positions[self.name] = node.positions[old_name]


class NetworkForm(BaseForm):
    action = "eNMS.base.processData"
    form_type = HiddenField(default="network")
    id = HiddenField()
    name = StringField("Name")
    creator = StringField(render_kw={"readonly": True})
    category = SelectField(
        "Category",
        choices=vs.dualize(vs.properties["property_list"]["network"]["category"]),
        validate_choice=False,
        default="Other",
    )
    latitude = StringField("Latitude", default=0.0)
    longitude = StringField("Longitude", default=0.0)
    networks = MultipleInstanceField("Networks", model="network")
    description = StringField(widget=TextArea(), render_kw={"rows": 6})

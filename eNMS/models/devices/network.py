from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import deferred, relationship

from eNMS.database import db
from eNMS.fields import HiddenField, SelectField
from eNMS.forms import DeviceForm
from eNMS.models.inventory import Device
from eNMS.variables import vs


class Network(Device):
    __tablename__ = class_type = "network"
    __mapper_args__ = {"polymorphic_identity": "network"}
    pretty_name = "Network"
    parent_type = "device"
    category = db.Column(db.SmallString)
    id = db.Column(Integer, ForeignKey(Device.id), primary_key=True)
    path = db.Column(db.TinyString)
    labels = db.Column(db.Dict, info={"log_change": False})
    positions = deferred(db.Column(db.Dict, info={"log_change": False}))
    devices = relationship(
        "Device", secondary=db.device_network_table, back_populates="networks"
    )
    links = relationship(
        "Link", secondary=db.link_network_table, back_populates="networks"
    )
    logs = relationship("Changelog", back_populates="network")
    device_changelogs = relationship(
        "Changelog",
        secondary=db.changelog_network_table,
        back_populates="networks",
        info={"log_change": False},
    )

    def duplicate(self, clone=None):
        for property in ("labels", "positions", "devices", "links"):
            setattr(clone, property, getattr(self, property))
        db.session.commit()
        return clone

    def post_update(self):
        if len(self.networks) == 1:
            self.path = f"{self.networks[0].path}>{self.id}"
        else:
            self.path = str(self.id)


class NetworkForm(DeviceForm):
    form_type = HiddenField(default="network")
    category = SelectField("Category")
    properties = ["category"]
    icon = SelectField(
        "Icon", choices=list(vs.visualization["icons"].items()), default="network"
    )

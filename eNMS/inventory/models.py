from re import search
from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    PickleType,
    String,
    Text,
    Float,
)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import backref, relationship
from typing import Any, Dict, List, Union

from eNMS.associations import (
    pool_device_table,
    pool_link_table,
    pool_user_table,
    job_device_table,
    job_pool_table,
)
from eNMS.functions import fetch, fetch_all
from eNMS.models import Base
from eNMS.properties import (
    custom_properties,
    pool_link_properties,
    pool_device_properties,
    sql_types,
)


class Object(Base):

    __tablename__ = "Object"
    type = Column(String(255))
    __mapper_args__ = {"polymorphic_identity": "Object", "polymorphic_on": type}
    id = Column(Integer, primary_key=True)
    hidden = Column(Boolean, default=False)
    name = Column(String(255), unique=True)
    subtype = Column(String(255))
    description = Column(String(255))
    model = Column(String(255))
    location = Column(String(255))
    vendor = Column(String(255))


CustomDevice: Any = (
    type(
        "CustomDevice",
        (Object,),
        {
            "__tablename__": "CustomDevice",
            "__mapper_args__": {"polymorphic_identity": "CustomDevice"},
            "id": Column(Integer, ForeignKey("Object.id"), primary_key=True),
            **{
                property: Column(sql_types[values["type"]], default=values["default"])
                for property, values in custom_properties.items()
            },
        },
    )
    if custom_properties
    else Object
)


class Device(CustomDevice):

    __tablename__ = "Device"
    __mapper_args__ = {"polymorphic_identity": "Device"}
    class_type = "device"
    id = Column(Integer, ForeignKey(CustomDevice.id), primary_key=True)
    operating_system = Column(String(255))
    os_version = Column(String(255))
    ip_address = Column(String(255))
    longitude = Column(Float)
    latitude = Column(Float)
    port = Column(Integer, default=22)
    username = Column(String(255))
    password = Column(String(255))
    enable_password = Column(String(255))
    netmiko_driver = Column(String(255))
    napalm_driver = Column(String(255))
    configurations = Column(MutableDict.as_mutable(PickleType), default={})
    current_configuration = Column(Text)
    last_failure = Column(String(255), default="Never")
    last_status = Column(String(255), default="Never")
    last_update = Column(String(255), default="Never")
    last_runtime = Column(Float, default=0.0)
    jobs = relationship("Job", secondary=job_device_table, back_populates="devices")
    pools = relationship("Pool", secondary=pool_device_table, back_populates="devices")

    @property
    def view_properties(self) -> Dict[str, Any]:
        return {
            property: getattr(self, property)
            for property in ("id", "name", "subtype", "latitude", "longitude")
        }

    def update(self, **kwargs: Any) -> None:
        super().update(**kwargs)
        if kwargs.get("dont_update_pools", False):
            return
        for pool in fetch_all("Pool"):
            if pool.never_update:
                continue
            if pool.object_match(self):
                pool.devices.append(self)
            elif self in pool.devices:
                pool.devices.remove(self)

    def generate_row(self, table: str) -> List[str]:
        if table == "device":
            return [
                f"""<button type="button" class="btn btn-info btn-xs"
                onclick="deviceAutomationModal('{self.id}')">
                Automation</button>""",
                f"""<button type="button" class="btn btn-success btn-xs"
                onclick="connectionParametersModal('{self.id}')">
                Connect</button>""",
                f"""<button type="button" class="btn btn-primary btn-xs"
                onclick="showTypeModal('device', '{self.id}')">Edit</button>""",
                f"""<button type="button" class="btn btn-primary btn-xs"
                onclick="showTypeModal('device', '{self.id}', true)">
                Duplicate</button>""",
                f"""<button type="button" class="btn btn-danger btn-xs"
                onclick="confirmDeletion('device', '{self.id}')">
                Delete</button>""",
            ]
        else:
            return [
                f"""<button type="button" class="btn btn-primary btn-xs"
                onclick="showConfigurations('{self.id}')">
                Configuration</button>"""
                if self.configurations
                else "",
                f"""<label class="btn btn-default btn-xs btn-file"
                style="width:100%;"><a href="download_configuration/{self.name}">
                Download</a></label>"""
                if self.configurations
                else "",
                f"""<button type="button" class="btn btn-primary btn-xs"
                onclick="showTypeModal('device', '{self.id}')">Edit</button>""",
            ]

    def __repr__(self) -> str:
        return f"{self.name} ({self.model})"


class Link(Object):

    __tablename__ = "Link"
    __mapper_args__ = {"polymorphic_identity": "Link"}
    class_type = "link"
    id = Column(Integer, ForeignKey("Object.id"), primary_key=True)
    source_id = Column(Integer, ForeignKey("Device.id"))
    destination_id = Column(Integer, ForeignKey("Device.id"))
    source = relationship(
        Device,
        primaryjoin=source_id == Device.id,
        backref=backref("source", cascade="all, delete-orphan"),
    )
    source_name = association_proxy("source", "name")
    destination = relationship(
        Device,
        primaryjoin=destination_id == Device.id,
        backref=backref("destination", cascade="all, delete-orphan"),
    )
    destination_name = association_proxy("destination", "name")
    pools = relationship("Pool", secondary=pool_link_table, back_populates="links")

    def __init__(self, **kwargs: Any) -> None:
        self.update(**kwargs)

    @property
    def view_properties(self) -> Dict[str, Any]:
        node_properties = ("id", "longitude", "latitude")
        return {
            **{
                property: getattr(self, property)
                for property in ("id", "name", "subtype")
            },
            **{
                f"source_{property}": getattr(self.source, property)
                for property in node_properties
            },
            **{
                f"destination_{property}": getattr(self.destination, property)
                for property in node_properties
            },
        }

    def update(self, **kwargs: Any) -> None:
        if "source_name" in kwargs:
            kwargs["source"] = fetch("Device", name=kwargs.pop("source_name")).id
            kwargs["destination"] = fetch(
                "Device", name=kwargs.pop("destination_name")
            ).id
        kwargs.update(
            {"source_id": kwargs["source"], "destination_id": kwargs["destination"]}
        )
        super().update(**kwargs)
        for pool in fetch_all("Pool"):
            if pool.never_update:
                continue
            if pool.object_match(self):
                pool.links.append(self)
            elif self in pool.links:
                pool.links.remove(self)

    def generate_row(self, table: str) -> List[str]:
        return [
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypeModal('link', '{self.id}')">Edit</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypeModal('link', '{self.id}', true)">Duplicate
            </button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="confirmDeletion('link', '{self.id}')">Delete</button>""",
        ]


AbstractPool: Any = type(
    "AbstractPool",
    (Base,),
    {
        "__tablename__": "AbstractPool",
        "type": "AbstractPool",
        "__mapper_args__": {"polymorphic_identity": "AbstractPool"},
        "id": Column(Integer, primary_key=True),
        **{
            **{
                f"device_{property}": Column(String(255))
                for property in pool_device_properties
            },
            **{
                f"device_{property}_match": Column(String(255), default="inclusion")
                for property in pool_device_properties
            },
            **{
                f"link_{property}": Column(String(255))
                for property in pool_link_properties
            },
            **{
                f"link_{property}_match": Column(String(255), default="inclusion")
                for property in pool_link_properties
            },
        },
    },
)


class Pool(AbstractPool):

    __tablename__ = type = "Pool"
    id = Column(Integer, ForeignKey("AbstractPool.id"), primary_key=True)
    name = Column(String(255), unique=True)
    description = Column(String(255))
    operator = Column(String(255), default="all")
    devices = relationship(
        "Device", secondary=pool_device_table, back_populates="pools"
    )
    links = relationship("Link", secondary=pool_link_table, back_populates="pools")
    latitude = Column(Float)
    longitude = Column(Float)
    jobs = relationship("Job", secondary=job_pool_table, back_populates="pools")
    users = relationship("User", secondary=pool_user_table, back_populates="pools")
    never_update = Column(Boolean, default=False)

    def update(self, **kwargs: Any) -> None:
        super().update(**kwargs)
        self.compute_pool()

    def generate_row(self, table: str) -> List[str]:
        return [
            f"""<button type="button" class="btn btn-info btn-xs"
            onclick="showPoolView('{self.id}')">
            Visualize</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypeModal('pool', '{self.id}')">
            Edit properties</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="updatePool('{self.id}')">Update</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypeModal('pool', '{self.id}', true)">
            Duplicate</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showPoolObjects('{self.id}')">Edit objects</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="confirmDeletion('pool', '{self.id}')">Delete</button>""",
        ]

    @property
    def object_number(self) -> str:
        return f"{len(self.devices)} devices - {len(self.links)} links"

    def property_match(self, obj: Union[Device, Link], property: str) -> bool:
        pool_value = getattr(self, f"{obj.class_type}_{property}")
        object_value = str(getattr(obj, property))
        match = getattr(self, f"{obj.class_type}_{property}_match")
        if not pool_value:
            return True
        elif match == "inclusion":
            return pool_value in object_value
        elif match == "equality":
            return pool_value == object_value
        else:
            return bool(search(pool_value, object_value))

    def object_match(self, obj: Union[Device, Link]) -> bool:
        properties = (
            pool_device_properties
            if obj.class_type == "device"
            else pool_link_properties
        )
        operator = all if self.operator == "all" else any
        return operator(self.property_match(obj, property) for property in properties)

    def compute_pool(self) -> None:
        if self.never_update:
            return
        self.devices = list(filter(self.object_match, Device.query.all()))
        self.links = list(filter(self.object_match, Link.query.all()))

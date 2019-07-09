from re import search
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import backref, relationship
from typing import Any, Dict, List, Union

from eNMS.controller import controller
from eNMS.database import (
    CustomMediumBlobPickle,
    LARGE_STRING_LENGTH,
    SMALL_STRING_LENGTH,
)
from eNMS.database.functions import fetch, fetch_all
from eNMS.database.associations import (
    pool_device_table,
    pool_link_table,
    pool_user_table,
    job_device_table,
    job_pool_table,
    task_device_table,
    task_pool_table,
)
from eNMS.database.base import AbstractBase
from eNMS.properties.objects import pool_link_properties, pool_device_properties


class Object(AbstractBase):

    __tablename__ = "Object"
    type = Column(String(SMALL_STRING_LENGTH), default="")
    __mapper_args__ = {"polymorphic_identity": "Object", "polymorphic_on": type}
    id = Column(Integer, primary_key=True)
    hidden = Column(Boolean, default=False)
    name = Column(String(SMALL_STRING_LENGTH), unique=True)
    subtype = Column(String(SMALL_STRING_LENGTH), default="")
    description = Column(String(SMALL_STRING_LENGTH), default="")
    model = Column(String(SMALL_STRING_LENGTH), default="")
    location = Column(String(SMALL_STRING_LENGTH), default="")
    vendor = Column(String(SMALL_STRING_LENGTH), default="")


CustomDevice: Any = type(
    "CustomDevice",
    (Object,),
    {
        "__tablename__": "CustomDevice",
        "__mapper_args__": {"polymorphic_identity": "CustomDevice"},
        "parent_cls": "Object",
        "id": Column(Integer, ForeignKey("Object.id"), primary_key=True),
        **{
            property: Column(
                {
                    "boolean": Boolean,
                    "float": Float,
                    "integer": Integer,
                    "string": Text(LARGE_STRING_LENGTH),
                }[values["type"]],
                default=values["default"],
            )
            for property, values in controller.custom_properties.items()
        },
    },
)


class Device(CustomDevice):

    __tablename__ = "Device"
    __mapper_args__ = {"polymorphic_identity": "Device"}
    class_type = "device"
    parent_cls = "CustomDevice"
    id = Column(Integer, ForeignKey(CustomDevice.id), primary_key=True)
    icon = Column(String(SMALL_STRING_LENGTH), default="router")
    operating_system = Column(String(SMALL_STRING_LENGTH), default="")
    os_version = Column(String(SMALL_STRING_LENGTH), default="")
    ip_address = Column(String(SMALL_STRING_LENGTH), default="")
    longitude = Column(Numeric(18, 8), default=0.0)
    latitude = Column(Numeric(18, 8), default=0.0)
    port = Column(Integer, default=22)
    username = Column(String(SMALL_STRING_LENGTH), default="")
    password = Column(String(SMALL_STRING_LENGTH), default="")
    enable_password = Column(String(SMALL_STRING_LENGTH), default="")
    netmiko_driver = Column(String(SMALL_STRING_LENGTH), default="cisco_ios")
    napalm_driver = Column(String(SMALL_STRING_LENGTH), default="ios")
    configurations = Column(MutableDict.as_mutable(CustomMediumBlobPickle), default={})
    current_configuration = Column(Text(LARGE_STRING_LENGTH))
    last_failure = Column(String(SMALL_STRING_LENGTH), default="Never")
    last_status = Column(String(SMALL_STRING_LENGTH), default="Never")
    last_update = Column(String(SMALL_STRING_LENGTH), default="Never")
    last_runtime = Column(Float, default=0.0)
    jobs = relationship("Job", secondary=job_device_table, back_populates="devices")
    tasks = relationship("Task", secondary=task_device_table, back_populates="devices")
    pools = relationship("Pool", secondary=pool_device_table, back_populates="devices")

    @property
    def view_properties(self) -> Dict[str, Any]:
        return {
            property: getattr(self, property)
            for property in ("id", "name", "icon", "latitude", "longitude")
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

    def get_configurations(self) -> dict:
        return {
            str(date): configuration
            for date, configuration in self.configurations.items()
        }

    def generate_row(self, table: str) -> List[str]:
        if table == "device":
            return [
                f"""<button type="button" class="btn btn-info btn-xs"
                onclick="showDeviceAutomationPanel({self.id})">
                Automation</button>""",
                f"""<button type="button" class="btn btn-success btn-xs"
                onclick="showPanel('connection', '{self.id}')">Connect</button>""",
                f"""<button type="button" class="btn btn-primary btn-xs"
                onclick="showTypePanel('device', '{self.id}')">Edit</button>""",
                f"""<button type="button" class="btn btn-primary btn-xs"
                onclick="showTypePanel('device', '{self.id}', true)">
                Duplicate</button>""",
                f"""<button type="button" class="btn btn-danger btn-xs"
                onclick="showDeletionPanel('device', '{self.id}', '{self.name}')">
                Delete</button>""",
            ]
        else:
            return [
                f"""<button type="button" class="btn btn-primary btn-xs"
                onclick="showConfigurationPanel('{self.id}', '{self.name}')">
                Configuration</button>"""
                if self.configurations
                else "",
                f"""<label class="btn btn-default btn-xs btn-file"
                style="width:100%;"><a href="/download_configuration/{self.name}">
                Download</a></label>"""
                if self.configurations
                else "",
                f"""<button type="button" class="btn btn-primary btn-xs"
                onclick="showTypePanel('device', '{self.id}')">Edit</button>""",
            ]

    def __repr__(self) -> str:
        return f"{self.name} ({self.model})"


class Link(Object):

    __tablename__ = "Link"
    __mapper_args__ = {"polymorphic_identity": "Link"}
    class_type = "link"
    parent_cls = "Object"
    id = Column(Integer, ForeignKey("Object.id"), primary_key=True)
    color = Column(String(SMALL_STRING_LENGTH), default="#000000")
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
                for property in ("id", "name", "color")
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
        if kwargs.get("dont_update_pools", False):
            return
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
            onclick="showTypePanel('link', '{self.id}')">Edit</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('link', '{self.id}', true)">Duplicate
            </button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="showDeletionPanel('link', '{self.id}'), '{self.name}'">
            Delete</button>""",
        ]


AbstractPool: Any = type(
    "AbstractPool",
    (AbstractBase,),
    {
        "__tablename__": "AbstractPool",
        "type": "AbstractPool",
        "__mapper_args__": {"polymorphic_identity": "AbstractPool"},
        "id": Column(Integer, primary_key=True),
        **{
            **{
                f"device_{property}": Column(Text(LARGE_STRING_LENGTH), default="")
                for property in pool_device_properties
            },
            **{
                f"device_{property}_match": Column(
                    String(SMALL_STRING_LENGTH), default="inclusion"
                )
                for property in pool_device_properties
            },
            **{
                f"link_{property}": Column(Text(LARGE_STRING_LENGTH), default="")
                for property in pool_link_properties
            },
            **{
                f"link_{property}_match": Column(
                    String(SMALL_STRING_LENGTH), default="inclusion"
                )
                for property in pool_link_properties
            },
        },
    },
)


class Pool(AbstractPool):

    __tablename__ = type = "Pool"
    parent_cls = "AbstractPool"
    id = Column(Integer, ForeignKey("AbstractPool.id"), primary_key=True)
    name = Column(String(SMALL_STRING_LENGTH), unique=True)
    last_modified = Column(String(SMALL_STRING_LENGTH), default="")
    description = Column(String(SMALL_STRING_LENGTH), default="")
    operator = Column(String(SMALL_STRING_LENGTH), default="all")
    devices = relationship(
        "Device", secondary=pool_device_table, back_populates="pools"
    )
    links = relationship("Link", secondary=pool_link_table, back_populates="pools")
    latitude = Column(Float, default=0.0)
    longitude = Column(Float, default=0.0)
    jobs = relationship("Job", secondary=job_pool_table, back_populates="pools")
    tasks = relationship("Task", secondary=task_pool_table, back_populates="pools")
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
            onclick="showTypePanel('pool', '{self.id}')">
            Edit</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="updatePools('{self.id}')">Update</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('pool', '{self.id}', true)">
            Duplicate</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showPoolObjectsPanel('{self.id}')">Edit objects</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="showDeletionPanel('pool', '{self.id}', '{self.name}')"
            >Delete</button>""",
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
        self.devices = list(filter(self.object_match, fetch_all("Device")))
        self.links = list(filter(self.object_match, fetch_all("Link")))

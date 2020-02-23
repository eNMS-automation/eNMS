from re import search, sub
from sqlalchemy import Boolean, Float, ForeignKey, Integer
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import UniqueConstraint

from eNMS import app
from eNMS.database.dialect import Column, LargeString, SmallString
from eNMS.database.functions import fetch, fetch_all
from eNMS.database.associations import (
    pool_device_table,
    pool_link_table,
    run_pool_table,
    run_device_table,
    service_device_table,
    service_pool_table,
    task_device_table,
    task_pool_table,
)
from eNMS.database.base import AbstractBase
from eNMS.setup import properties


class Object(AbstractBase):

    __tablename__ = "object"
    type = Column(SmallString)
    __mapper_args__ = {"polymorphic_identity": "object", "polymorphic_on": type}
    id = Column(Integer, primary_key=True)
    last_modified = Column(SmallString, info={"dont_track_changes": True})
    subtype = Column(SmallString)
    description = Column(SmallString)
    model = Column(SmallString)
    location = Column(SmallString)
    vendor = Column(SmallString)

    def update(self, **kwargs):
        super().update(**kwargs)
        if kwargs.get("dont_update_pools", False):
            return
        for pool in fetch_all("pool"):
            if pool.never_update:
                continue
            match = pool.object_match(self)
            relation, number = f"{self.class_type}s", f"{self.class_type}_number"
            if match and self not in getattr(pool, relation):
                getattr(pool, relation).append(self)
                setattr(pool, number, getattr(pool, number) + 1)
            if self in getattr(pool, relation) and not match:
                getattr(pool, relation).remove(self)
                setattr(pool, number, getattr(pool, number) - 1)

    def delete(self):
        number = f"{self.class_type}_number"
        for pool in self.pools:
            setattr(pool, number, getattr(pool, number) - 1)


CustomDevice = type(
    "CustomDevice",
    (Object,),
    {
        "__tablename__": "custom_device",
        "__mapper_args__": {"polymorphic_identity": "custom_device"},
        "parent_type": "object",
        "id": Column(Integer, ForeignKey("object.id"), primary_key=True),
        **{
            property: Column(
                {
                    "boolean": Boolean,
                    "float": Float,
                    "integer": Integer,
                    "string": LargeString,
                }[values["type"]],
                default=values["default"],
            )
            for property, values in app.properties["custom"]["device"].items()
        },
    },
)


class Device(CustomDevice):

    __tablename__ = "device"
    __mapper_args__ = {"polymorphic_identity": "device"}
    class_type = "device"
    parent_type = "custom_device"
    id = Column(Integer, ForeignKey(CustomDevice.id), primary_key=True)
    name = Column(SmallString, unique=True)
    icon = Column(SmallString, default="router")
    operating_system = Column(SmallString)
    os_version = Column(SmallString)
    ip_address = Column(SmallString)
    longitude = Column(SmallString, default="0.0")
    latitude = Column(SmallString, default="0.0")
    port = Column(Integer, default=22)
    username = Column(SmallString)
    password = Column(SmallString)
    enable_password = Column(SmallString)
    netmiko_driver = Column(SmallString, default="cisco_ios")
    napalm_driver = Column(SmallString, default="ios")
    configuration = Column(LargeString, info={"dont_track_changes": True})
    operational_data = Column(LargeString, info={"dont_track_changes": True})
    last_failure = Column(SmallString, default="Never")
    last_status = Column(SmallString, default="Never")
    last_update = Column(SmallString, default="Never")
    last_runtime = Column(SmallString)
    last_duration = Column(SmallString)
    services = relationship(
        "Service", secondary=service_device_table, back_populates="devices"
    )
    runs = relationship(
        "Run",
        secondary=run_device_table,
        back_populates="devices",
        cascade="all,delete",
    )
    tasks = relationship("Task", secondary=task_device_table, back_populates="devices")
    pools = relationship("Pool", secondary=pool_device_table, back_populates="devices")
    sessions = relationship(
        "Session", back_populates="device", cascade="all, delete-orphan"
    )

    def table_properties(self, **kwargs):
        properties = super().get_properties()
        context = int(kwargs["form"].get("context-lines", 0))
        for property in ("configuration", "operational_data"):
            data = kwargs["form"].get(property)
            regex_match = kwargs["form"].get(f"{property}_filter") == "regex"
            if not data:
                properties[property] = ""
            else:
                result = []
                content, visited = getattr(self, property).splitlines(), set()
                for (index, line) in enumerate(content):
                    match_lines, merge = [], index - context - 1 in visited
                    if not search(data, line) if regex_match else data not in line:
                        continue
                    for i in range(-context, context + 1):
                        if index + i < 0 or index + i > len(content) - 1:
                            continue
                        if index + i in visited:
                            merge = True
                            continue
                        visited.add(index + i)
                        if regex_match:
                            line = sub(data, r"<mark>\g<0></mark>", content[index + i])
                        else:
                            line = (
                                content[index + i]
                                .strip()
                                .replace(data, f"<mark>{data}</mark>")
                            )
                        match_lines.append(f"<b>L{index + i + 1}:</b> {line}")
                    if merge:
                        result[-1] += f"<br>{'<br>'.join(match_lines)}"
                    else:
                        result.append("<br>".join(match_lines))
                properties[property] = "".join(
                    f"<pre style='text-align: left'>{match}</pre>" for match in result
                )
        return properties

    @property
    def view_properties(self):
        return {
            property: getattr(self, property)
            for property in ("id", "type", "name", "icon", "latitude", "longitude")
        }

    @property
    def ui_name(self):
        return f"{self.name} ({self.model})" if self.model else self.name

    def __repr__(self):
        return f"{self.name} ({self.model})" if self.model else self.name


class Link(Object):

    __tablename__ = "link"
    __mapper_args__ = {"polymorphic_identity": "link"}
    class_type = "link"
    parent_type = "object"
    id = Column(Integer, ForeignKey("object.id"), primary_key=True)
    name = Column(SmallString)
    color = Column(SmallString, default="#000000")
    source_id = Column(Integer, ForeignKey("device.id"))
    destination_id = Column(Integer, ForeignKey("device.id"))
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
    __table_args__ = (UniqueConstraint(name, source_id, destination_id),)

    def __init__(self, **kwargs):
        self.update(**kwargs)

    @property
    def view_properties(self):
        node_properties = ("id", "longitude", "latitude")
        return {
            **{
                property: getattr(self, property)
                for property in ("id", "type", "name", "color")
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

    def update(self, **kwargs):
        if "source_name" in kwargs:
            kwargs["source"] = fetch("device", name=kwargs.pop("source_name")).id
            kwargs["destination"] = fetch(
                "device", name=kwargs.pop("destination_name")
            ).id
        kwargs.update(
            {"source_id": kwargs["source"], "destination_id": kwargs["destination"]}
        )
        super().update(**kwargs)


AbstractPool = type(
    "AbstractPool",
    (AbstractBase,),
    {
        "__tablename__": "abstract_pool",
        "type": "pool",
        "__mapper_args__": {"polymorphic_identity": "abstract_pool"},
        "id": Column(Integer, primary_key=True),
        **{
            **{
                f"device_{property}": Column(LargeString, default="")
                for property in properties["filtering"]["device"]
            },
            **{
                f"device_{property}_match": Column(SmallString, default="inclusion")
                for property in properties["filtering"]["device"]
            },
            **{
                f"link_{property}": Column(LargeString, default="")
                for property in properties["filtering"]["link"]
            },
            **{
                f"link_{property}_match": Column(SmallString, default="inclusion")
                for property in properties["filtering"]["link"]
            },
        },
    },
)


class Pool(AbstractPool):

    __tablename__ = "pool"
    parent_type = "abstract_pool"
    id = Column(Integer, ForeignKey("abstract_pool.id"), primary_key=True)
    name = Column(SmallString, unique=True)
    last_modified = Column(SmallString, info={"dont_track_changes": True})
    description = Column(SmallString)
    operator = Column(SmallString, default="all")
    devices = relationship(
        "Device", secondary=pool_device_table, back_populates="pools"
    )
    device_number = Column(Integer, default=0)
    links = relationship("Link", secondary=pool_link_table, back_populates="pools")
    link_number = Column(Integer, default=0)
    latitude = Column(SmallString, default="0.0")
    longitude = Column(SmallString, default="0.0")
    services = relationship(
        "Service", secondary=service_pool_table, back_populates="pools"
    )
    runs = relationship("Run", secondary=run_pool_table, back_populates="pools")
    tasks = relationship("Task", secondary=task_pool_table, back_populates="pools")
    never_update = Column(Boolean, default=False)

    def update(self, **kwargs):
        super().update(**kwargs)
        self.compute_pool()

    def property_match(self, obj, property):
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

    def object_match(self, obj):
        operator = all if self.operator == "all" else any
        return operator(
            self.property_match(obj, property)
            for property in properties["filtering"][obj.class_type]
        )

    def compute_pool(self):
        if self.never_update:
            return
        self.devices = list(filter(self.object_match, fetch_all("device")))
        self.device_number = len(self.devices)
        self.links = list(filter(self.object_match, fetch_all("link")))
        self.link_number = len(self.links)


class Session(AbstractBase):

    __tablename__ = type = "session"
    private = True
    id = Column(Integer, primary_key=True)
    name = Column(SmallString, unique=True)
    timestamp = Column(SmallString)
    user = Column(SmallString)
    content = Column(LargeString, info={"dont_track_changes": True})
    device_id = Column(Integer, ForeignKey("device.id"))
    device = relationship(
        "Device", back_populates="sessions", foreign_keys="Session.device_id"
    )
    device_name = association_proxy("device", "name")

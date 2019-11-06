from re import search
from sqlalchemy import Boolean, Float, ForeignKey, Integer
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import backref, relationship

from eNMS import app
from eNMS.database.dialect import Column, LargeString, SmallString
from eNMS.database.functions import fetch, fetch_all
from eNMS.database.associations import (
    pool_device_table,
    pool_link_table,
    pool_user_table,
    run_pool_table,
    run_device_table,
    service_device_table,
    service_pool_table,
    task_device_table,
    task_pool_table,
)
from eNMS.database.base import AbstractBase
from eNMS.properties.objects import pool_link_properties, pool_device_properties


class Object(AbstractBase):

    __tablename__ = "object"
    type = Column(SmallString)
    __mapper_args__ = {"polymorphic_identity": "object", "polymorphic_on": type}
    id = Column(Integer, primary_key=True)
    name = Column(SmallString, unique=True)
    subtype = Column(SmallString)
    description = Column(SmallString)
    model = Column(SmallString)
    location = Column(SmallString)
    vendor = Column(SmallString)


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
            for property, values in app.custom_properties.items()
        },
    },
)


class Device(CustomDevice):

    __tablename__ = "device"
    __mapper_args__ = {"polymorphic_identity": "device"}
    class_type = "device"
    parent_type = "custom_device"
    id = Column(Integer, ForeignKey(CustomDevice.id), primary_key=True)
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
    configuration = Column(LargeString)
    operational_data = Column(LargeString)
    last_failure = Column(SmallString, default="Never")
    last_status = Column(SmallString, default="Never")
    last_update = Column(SmallString, default="Never")
    last_runtime = Column(SmallString)
    last_duration = Column(SmallString)
    services = relationship(
        "Service", secondary=service_device_table, back_populates="devices"
    )
    runs = relationship("Run", secondary=run_device_table, back_populates="devices")
    tasks = relationship("Task", secondary=task_device_table, back_populates="devices")
    pools = relationship("Pool", secondary=pool_device_table, back_populates="devices")

    @property
    def view_properties(self):
        return {
            property: getattr(self, property)
            for property in ("id", "name", "icon", "latitude", "longitude")
        }

    @property
    def ui_name(self):
        return f"{self.name} ({self.model})" if self.model else self.name

    def update(self, **kwargs):
        super().update(**kwargs)
        if kwargs.get("dont_update_pools", False):
            return
        for pool in fetch_all("pool"):
            if pool.never_update:
                continue
            match = pool.object_match(self)
            if match and self not in pool.devices:
                pool.devices.append(self)
                pool.device_number += 1
            if self in pool.devices and not match:
                pool.devices.remove(self)
                pool.device_number -= 1

    def generate_row(self, table):
        return [
            f"""
            <ul class="pagination pagination-lg" style="margin: 0px; width: 300px">
          <li>
            <button type="button" class="btn btn-info"
            onclick="showDeviceNetworkData({self.row_properties})"
            data-tooltip="Network Data"
              ><span class="glyphicon glyphicon-cog"></span
            ></button>
          </li>
          <li>
            <button type="button" class="btn btn-info"
            onclick="showDeviceResultsPanel({self.row_properties})"
            data-tooltip="Results"
              ><span class="glyphicon glyphicon-list-alt"></span
            ></button>
          </li>
          <li>
            <button type="button" class="btn btn-success"
            onclick="showPanel('device_connection', '{self.id}')"
            data-tooltip="Connection"
              ><span class="glyphicon glyphicon-console"></span
            ></button>
          </li>
          <li>
            <button type="button" class="btn btn-primary"
            onclick="showTypePanel('device', '{self.id}')" data-tooltip="Edit"
              ><span class="glyphicon glyphicon-edit"></span
            ></button>
          </li>
          <li>
            <button type="button" class="btn btn-primary"
            onclick="showTypePanel('device', '{self.id}', 'duplicate')"
            data-tooltip="Duplicate"
              ><span class="glyphicon glyphicon-duplicate"></span
            ></button>
          </li>
          <li>
            <button type="button" class="btn btn-danger"
            onclick="showDeletionPanel({self.row_properties})" data-tooltip="Delete"
              ><span class="glyphicon glyphicon-trash"></span
            ></button>
          </li>
        </ul>"""
        ]

    def __repr__(self):
        return f"{self.name} ({self.model})" if self.model else self.name


class Link(Object):

    __tablename__ = "link"
    __mapper_args__ = {"polymorphic_identity": "link"}
    class_type = "link"
    parent_type = "object"
    id = Column(Integer, ForeignKey("object.id"), primary_key=True)
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

    def __init__(self, **kwargs):
        self.update(**kwargs)

    @property
    def view_properties(self):
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
        if kwargs.get("dont_update_pools", False):
            return
        for pool in fetch_all("pool"):
            if pool.never_update:
                continue
            if pool.object_match(self):
                pool.links.append(self)
            elif self in pool.links:
                pool.links.remove(self)

    def generate_row(self, table):
        return [
            f"""
            <ul class="pagination pagination-lg" style="margin: 0px; width: 150px">
          <li>
            <button type="button" class="btn btn-primary"
            onclick="showTypePanel('link', '{self.id}')" data-tooltip="Edit"
              ><span class="glyphicon glyphicon-edit"></span
            ></button>
          </li>
          <li>
            <button type="button" class="btn btn-primary"
            onclick="showTypePanel('link', '{self.id}', 'duplicate')"
            data-tooltip="Duplicate"
              ><span class="glyphicon glyphicon-duplicate"></span
            ></button>
          </li>
          <li>
            <button type="button" class="btn btn-danger"
            onclick="showDeletionPanel({self.row_properties})" data-tooltip="Delete"
              ><span class="glyphicon glyphicon-trash"></span
            ></button>
          </li>
        </ul>"""
        ]


AbstractPool = type(
    "AbstractPool",
    (AbstractBase,),
    {
        "__tablename__": "abstract_pool",
        "type": "abstract_pool",
        "__mapper_args__": {"polymorphic_identity": "abstract_pool"},
        "id": Column(Integer, primary_key=True),
        **{
            **{
                f"device_{property}": Column(LargeString, default="")
                for property in pool_device_properties
            },
            **{
                f"device_{property}_match": Column(SmallString, default="inclusion")
                for property in pool_device_properties
            },
            **{
                f"link_{property}": Column(LargeString, default="")
                for property in pool_link_properties
            },
            **{
                f"link_{property}_match": Column(SmallString, default="inclusion")
                for property in pool_link_properties
            },
        },
    },
)


class Pool(AbstractPool):

    __tablename__ = type = "pool"
    parent_type = "abstract_pool"
    id = Column(Integer, ForeignKey("abstract_pool.id"), primary_key=True)
    name = Column(SmallString, unique=True)
    last_modified = Column(SmallString)
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
    users = relationship("User", secondary=pool_user_table, back_populates="pools")
    never_update = Column(Boolean, default=False)

    def update(self, **kwargs):
        super().update(**kwargs)
        self.compute_pool()

    def generate_row(self, table):
        return [
            f"""
            <ul class="pagination pagination-lg" style="margin: 0px; width: 300px">
          <li>
            <button type="button" class="btn btn-info"
            onclick="showPoolView('{self.id}')" data-tooltip="Internal View"
              ><span class="glyphicon glyphicon-eye-open"></span
            ></button>
          </li>
          <li>
            <button type="button" class="btn btn-primary"
            onclick="showPoolObjectsPanel('{self.id}')" data-tooltip="Pool Objects"
              ><span class="glyphicon glyphicon-wrench"></span
            ></button>
          </li>
          <li>
            <button type="button" class="btn btn-primary"
            onclick="updatePools('{self.id}')" data-tooltip="Update"
              ><span class="glyphicon glyphicon-refresh"></span
            ></button>
          </li>
          <li>
            <button type="button" class="btn btn-primary"
            onclick="showTypePanel('pool', '{self.id}')" data-tooltip="Edit"
              ><span class="glyphicon glyphicon-edit"></span
            ></button>
          </li>
          <li>
            <button type="button" class="btn btn-primary"
            onclick="showTypePanel('pool', '{self.id}', 'duplicate')"
            data-tooltip="Duplicate"
              ><span class="glyphicon glyphicon-duplicate"></span
            ></button>
          </li>
          <li>
            <button type="button" class="btn btn-danger"
            onclick="showDeletionPanel({self.row_properties})" data-tooltip="Delete"
              ><span class="glyphicon glyphicon-trash"></span
            ></button>
          </li></ul>"""
        ]

    @property
    def object_number(self):
        return f"{self.device_number} devices - {self.link_number} links"

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
        properties = (
            pool_device_properties
            if obj.class_type == "device"
            else pool_link_properties
        )
        operator = all if self.operator == "all" else any
        return operator(self.property_match(obj, property) for property in properties)

    def compute_pool(self):
        if self.never_update:
            return
        self.devices = list(filter(self.object_match, fetch_all("device")))
        self.device_number = len(self.devices)
        self.links = list(filter(self.object_match, fetch_all("link")))
        self.link_number = len(self.links)

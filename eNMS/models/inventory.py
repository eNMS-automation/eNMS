from flask_login import current_user
from re import search, sub
from sqlalchemy import and_, Boolean, ForeignKey, Integer, or_
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import aliased, backref, relationship
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.sql.expression import true

from eNMS import app
from eNMS.models import models
from eNMS.models.base import AbstractBase
from eNMS.database import db
from eNMS.setup import properties


class Object(AbstractBase):

    __tablename__ = "object"
    type = db.Column(db.SmallString)
    __mapper_args__ = {"polymorphic_identity": "object", "polymorphic_on": type}
    id = db.Column(Integer, primary_key=True)
    public = db.Column(Boolean)
    last_modified = db.Column(db.SmallString, info={"log_change": False})
    subtype = db.Column(db.SmallString)
    description = db.Column(db.SmallString)
    model = db.Column(db.SmallString)
    location = db.Column(db.SmallString)
    vendor = db.Column(db.SmallString)

    def update(self, **kwargs):
        super().update(**kwargs)
        if kwargs.get("dont_update_pools", False):
            return
        for pool in db.fetch_all("pool"):
            if pool.manually_defined or not pool.compute(self.class_type):
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

    @classmethod
    def rbac_filter(cls, query, mode, user):
        pool_alias = aliased(models["pool"])
        return query.filter(cls.public == true()).union(
            query.join(cls.pools)
            .join(models["access"], models["pool"].access)
            .join(pool_alias, models["access"].user_pools)
            .join(models["user"], pool_alias.users)
            .filter(models["access"].access_type.contains(mode))
            .filter(models["user"].name == user.name)
        )


@db.set_custom_properties
class Device(Object):

    __tablename__ = class_type = "device"
    __mapper_args__ = {"polymorphic_identity": "device"}
    parent_type = "object"
    id = db.Column(Integer, ForeignKey(Object.id), primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    icon = db.Column(db.SmallString, default="router")
    operating_system = db.Column(db.SmallString)
    os_version = db.Column(db.SmallString)
    ip_address = db.Column(db.SmallString)
    longitude = db.Column(db.SmallString, default="0.0")
    latitude = db.Column(db.SmallString, default="0.0")
    port = db.Column(Integer, default=22)
    username = db.Column(db.SmallString)
    password = db.Column(db.SmallString)
    enable_password = db.Column(db.SmallString)
    netmiko_driver = db.Column(db.SmallString, default="cisco_ios")
    napalm_driver = db.Column(db.SmallString, default="ios")
    scrapli_driver = db.Column(db.SmallString, default="cisco_iosxe")
    configuration = db.Column(db.LargeString, info={"log_change": False})
    last_failure = db.Column(db.SmallString, default="Never")
    last_status = db.Column(db.SmallString, default="Never")
    last_update = db.Column(db.SmallString, default="Never")
    last_runtime = db.Column(db.SmallString)
    last_duration = db.Column(db.SmallString)
    services = relationship(
        "Service",
        secondary=db.service_target_device_table,
        back_populates="target_devices",
    )
    runs = relationship(
        "Run",
        secondary=db.run_device_table,
        back_populates="target_devices",
        cascade="all,delete",
    )
    tasks = relationship(
        "Task", secondary=db.task_device_table, back_populates="devices"
    )
    pools = relationship(
        "Pool", secondary=db.pool_device_table, back_populates="devices"
    )
    sessions = relationship(
        "Session", back_populates="device", cascade="all, delete-orphan"
    )

    def get_neighbors(self, object_type, direction="both", **link_constraints):
        filters = [models["link"].destination == self, models["link"].source == self]
        edge_constraints = (
            filters if direction == "both" else [filters[direction == "source"]]
        )
        link_constraints = [
            getattr(models["link"], key) == value
            for key, value in link_constraints.items()
        ]
        neighboring_links = (
            db.query("link")
            .filter(and_(or_(*edge_constraints), *link_constraints))
            .all()
        )
        if "link" in object_type:
            return neighboring_links
        else:
            return list(
                set(
                    link.destination if link.source == self else link.source
                    for link in neighboring_links
                )
            )

    def table_properties(self, **kwargs):
        columns = [c["data"] for c in kwargs["columns"]]
        rest_api_request = kwargs.get("rest_api_request")
        include_properties = columns if rest_api_request else None
        properties = super().get_properties(include=include_properties)
        context = int(kwargs["form"].get("context-lines", 0))
        for property in app.configuration_properties:
            if rest_api_request:
                if property in columns:
                    properties[property] = getattr(self, property)
                if f"{property}_matches" not in columns:
                    continue
            data = kwargs["form"].get(property)
            regex_match = kwargs["form"].get(f"{property}_filter") == "regex"
            if not data:
                properties[property] = ""
            else:
                result = []
                content, visited = getattr(self, property).splitlines(), set()
                for (index, line) in enumerate(content):
                    match_lines, merge = [], index - context - 1 in visited
                    if (
                        not search(data, line)
                        if regex_match
                        else data.lower() not in line.lower()
                    ):
                        continue
                    for i in range(-context, context + 1):
                        if index + i < 0 or index + i > len(content) - 1:
                            continue
                        if index + i in visited:
                            merge = True
                            continue
                        visited.add(index + i)
                        line = content[index + i].strip()
                        if rest_api_request:
                            match_lines.append(f"L{index + i + 1}: {line}")
                            continue
                        line = sub(f"(?i){data}", r"<mark>\g<0></mark>", line)
                        match_lines.append(f"<b>L{index + i + 1}:</b> {line}")
                    if rest_api_request:
                        result.extend(match_lines)
                    else:
                        if merge:
                            result[-1] += f"<br>{'<br>'.join(match_lines)}"
                        else:
                            result.append("<br>".join(match_lines))
                if rest_api_request:
                    properties[f"{property}_matches"] = result
                else:
                    properties[property] = "".join(
                        f"<pre style='text-align: left'>{match}</pre>"
                        for match in result
                    )
        return properties

    @property
    def view_properties(self):
        return {
            property: getattr(self, property)
            for property in (
                "id",
                "type",
                "name",
                "icon",
                "latitude",
                "longitude",
                "last_runtime",
            )
        }

    @property
    def ui_name(self):
        return f"{self.name} ({self.model})" if self.model else self.name

    def __repr__(self):
        return f"{self.name} ({self.model})" if self.model else self.name


@db.set_custom_properties
class Link(Object):

    __tablename__ = class_type = "link"
    __mapper_args__ = {"polymorphic_identity": "link"}
    parent_type = "object"
    id = db.Column(Integer, ForeignKey("object.id"), primary_key=True)
    name = db.Column(db.SmallString)
    color = db.Column(db.SmallString, default="#000000")
    source_id = db.Column(Integer, ForeignKey("device.id"))
    destination_id = db.Column(Integer, ForeignKey("device.id"))
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
    pools = relationship("Pool", secondary=db.pool_link_table, back_populates="links")
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
            kwargs["source"] = db.fetch("device", name=kwargs.pop("source_name")).id
            kwargs["destination"] = db.fetch(
                "device", name=kwargs.pop("destination_name")
            ).id
        if "source" in kwargs and "destination" in kwargs:
            kwargs.update(
                {"source_id": kwargs["source"], "destination_id": kwargs["destination"]}
            )
        super().update(**kwargs)


def set_pool_properties(Pool):
    for model in Pool.models:
        for property in properties["filtering"][model]:
            setattr(Pool, f"{model}_{property}", db.Column(db.LargeString))
            setattr(
                Pool,
                f"{model}_{property}_match",
                db.Column(db.SmallString, default="inclusion"),
            )
        setattr(
            Pool,
            f"{model}s",
            relationship(
                model.capitalize(),
                secondary=getattr(db, f"pool_{model}_table"),
                back_populates="pools",
            ),
        )
        setattr(Pool, f"{model}_number", db.Column(Integer, default=0))
    return Pool


@set_pool_properties
@db.set_custom_properties
class Pool(AbstractBase):

    __tablename__ = type = "pool"
    models = ("device", "link", "service", "user")
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    public = db.Column(Boolean)
    last_modified = db.Column(db.SmallString, info={"log_change": False})
    description = db.Column(db.SmallString)
    operator = db.Column(db.SmallString, default="all")
    latitude = db.Column(db.SmallString, default="0.0")
    longitude = db.Column(db.SmallString, default="0.0")
    target_services = relationship(
        "Service", secondary=db.service_target_pool_table, back_populates="target_pools"
    )
    visualization_default = db.Column(Boolean)
    runs = relationship(
        "Run", secondary=db.run_pool_table, back_populates="target_pools"
    )
    tasks = relationship("Task", secondary=db.task_pool_table, back_populates="pools")
    access_users = relationship(
        "Access", secondary=db.access_user_pools_table, back_populates="user_pools"
    )
    access = relationship(
        "Access", secondary=db.access_model_pools_table, back_populates="access_pools"
    )
    manually_defined = db.Column(Boolean, default=False)

    def update(self, **kwargs):
        old_users = set(self.users)
        super().update(**kwargs)
        self.compute_pool()
        if not getattr(current_user, "is_admin", True):
            current_user.add_access("pools", self)
        for user in old_users | set(self.users):
            user.update_rbac()

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

    def compute(self, model):
        return any(
            getattr(self, f"{model}_{property}")
            for property in properties["filtering"][model]
        )

    def compute_pool(self):
        if self.manually_defined:
            return
        for model in self.models:
            objects = (
                list(filter(self.object_match, db.fetch_all(model)))
                if self.compute(model)
                else []
            )
            setattr(self, f"{model}s", objects)
            setattr(self, f"{model}_number", len(objects))

    @classmethod
    def rbac_filter(cls, query, mode, user):
        pool_alias = aliased(models["pool"])
        return query.filter(cls.public == true()).union(
            query.join(cls.access)
            .join(pool_alias, models["access"].user_pools)
            .join(models["user"], pool_alias.users)
            .filter(models["access"].access_type.contains(mode))
        )


class Session(AbstractBase):

    __tablename__ = type = "session"
    private = True
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    timestamp = db.Column(db.SmallString)
    user = db.Column(db.SmallString)
    content = db.Column(db.LargeString, info={"log_change": False})
    device_id = db.Column(Integer, ForeignKey("device.id"))
    device = relationship(
        "Device", back_populates="sessions", foreign_keys="Session.device_id"
    )
    device_name = association_proxy("device", "name")

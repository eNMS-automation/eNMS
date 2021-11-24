from re import search, sub
from sqlalchemy import and_, Boolean, event, Float, ForeignKey, Integer, or_
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import aliased, backref, relationship
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.sql.expression import false

from eNMS.controller import controller
from eNMS.models.base import AbstractBase
from eNMS.database import db
from eNMS.variables import vs


class Object(AbstractBase):

    __tablename__ = "object"
    pool_model = True
    type = db.Column(db.SmallString)
    __mapper_args__ = {"polymorphic_identity": "object", "polymorphic_on": type}
    id = db.Column(Integer, primary_key=True)
    creator = db.Column(db.SmallString)
    access_groups = db.Column(db.LargeString)
    last_modified = db.Column(db.TinyString, info={"log_change": False})
    subtype = db.Column(db.SmallString)
    description = db.Column(db.LargeString)
    model = db.Column(db.SmallString)
    location = db.Column(db.SmallString)
    vendor = db.Column(db.SmallString)

    def delete(self):
        number = f"{self.class_type}_number"
        for pool in self.pools:
            setattr(pool, number, getattr(pool, number) - 1)

    @classmethod
    def rbac_filter(cls, query, mode, user):
        pool_alias = aliased(vs.models["pool"])
        return (
            query.join(cls.pools)
            .join(vs.models["access"], vs.models["pool"].access)
            .join(pool_alias, vs.models["access"].user_pools)
            .join(vs.models["user"], pool_alias.users)
            .filter(vs.models["access"].access_type.contains(mode))
            .filter(vs.models["user"].name == user.name)
            .group_by(cls.id)
        )


class Device(Object):

    __tablename__ = class_type = "device"
    __mapper_args__ = {"polymorphic_identity": "device"}
    parent_type = "object"
    id = db.Column(Integer, ForeignKey(Object.id), primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    icon = db.Column(db.TinyString, default="router")
    operating_system = db.Column(db.SmallString)
    os_version = db.Column(db.SmallString)
    ip_address = db.Column(db.TinyString)
    longitude = db.Column(db.TinyString, default="0.0")
    latitude = db.Column(db.TinyString, default="0.0")
    port = db.Column(Integer, default=22)
    netmiko_driver = db.Column(db.TinyString, default="cisco_ios")
    napalm_driver = db.Column(db.TinyString, default="ios")
    scrapli_driver = db.Column(db.TinyString, default="cisco_iosxe")
    netconf_driver = db.Column(db.TinyString, default="default")
    configuration = db.Column(db.LargeString, info={"log_change": False})
    target_services = relationship(
        "Service",
        secondary=db.service_target_device_table,
        back_populates="target_devices",
    )
    runs = relationship(
        "Run", secondary=db.run_device_table, back_populates="target_devices"
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

    @classmethod
    def database_init(cls):
        for property in vs.configuration_properties:
            for timestamp in vs.timestamps:
                column = db.Column(db.SmallString, default="Never")
                setattr(cls, f"last_{property}_{timestamp}", column)
        return cls

    def get_neighbors(self, object_type, direction="both", **link_constraints):
        filters = [
            vs.models["link"].destination == self,
            vs.models["link"].source == self,
        ]
        edge_constraints = (
            filters if direction == "both" else [filters[direction == "source"]]
        )
        link_constraints = [
            getattr(vs.models["link"], key) == value
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
        columns = [column["data"] for column in kwargs["columns"]]
        rest_api_request = kwargs.get("rest_api_request")
        include_properties = columns if rest_api_request else None
        properties = super().get_properties(include=include_properties)
        context = int(kwargs["form"].get("context-lines", 0))
        for property in vs.configuration_properties:
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
        properties = (
            "id",
            "type",
            "name",
            "icon",
            "latitude",
            "longitude",
        )
        return {property: getattr(self, property) for property in properties}

    @property
    def ui_name(self):
        return f"{self.name} ({self.model})" if self.model else str(self.name)

    def __repr__(self):
        return f"{self.name} ({self.model})" if self.model else str(self.name)


class Link(Object):

    __tablename__ = class_type = "link"
    __mapper_args__ = {"polymorphic_identity": "link"}
    parent_type = "object"
    id = db.Column(Integer, ForeignKey("object.id"), primary_key=True)
    name = db.Column(db.SmallString)
    color = db.Column(db.TinyString, default="#000000")
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
                f"source_{property}": getattr(self.source, property, None)
                for property in node_properties
            },
            **{
                f"destination_{property}": getattr(self.destination, property, None)
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


class Pool(AbstractBase):

    __tablename__ = type = "pool"
    models = ("device", "link", "service", "user")
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    manually_defined = db.Column(Boolean, default=False)
    creator = db.Column(db.SmallString)
    access_groups = db.Column(db.LargeString)
    admin_only = db.Column(Boolean, default=False)
    last_modified = db.Column(db.TinyString, info={"log_change": False})
    description = db.Column(db.LargeString)
    target_services = relationship(
        "Service", secondary=db.service_target_pool_table, back_populates="target_pools"
    )
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
    credential_devices = relationship(
        "Credential",
        secondary=db.credential_device_table,
        back_populates="device_pools",
    )
    credential_users = relationship(
        "Credential",
        secondary=db.credential_user_table,
        back_populates="user_pools",
    )

    @classmethod
    def configure_events(cls):
        for model in cls.models:

            @event.listens_for(getattr(cls, f"{model}s"), "append")
            def append(target, value, _):
                number = getattr(target, f"{value.class_type}_number") or 0
                setattr(target, f"{value.class_type}_number", number + 1)

            @event.listens_for(getattr(cls, f"{model}s"), "remove")
            def remove(target, value, _):
                number = getattr(target, f"{value.class_type}_number")
                setattr(target, f"{value.class_type}_number", number - 1)

    @classmethod
    def database_init(cls):
        for model in cls.models:
            for property in vs.properties["filtering"][model]:
                setattr(cls, f"{model}_{property}", db.Column(db.LargeString))
                setattr(
                    cls,
                    f"{model}_{property}_match",
                    db.Column(db.TinyString, default="inclusion"),
                )
                setattr(
                    cls, f"{model}_{property}_invert", db.Column(Boolean, default=False)
                )
            setattr(
                cls,
                f"{model}s",
                relationship(
                    model.capitalize(),
                    secondary=getattr(db, f"pool_{model}_table"),
                    back_populates="pools",
                ),
            )
            setattr(cls, f"{model}_number", db.Column(Integer, default=0))

    def update(self, **kwargs):
        old_users = set(self.users)
        super().update(**kwargs)
        if not kwargs.get("import_mechanism", False):
            self.compute_pool()
            for user in set(self.users) | old_users:
                user.update_rbac()

    def match_instance(self, instance):
        match_list = []
        for property in vs.properties["filtering"][instance.class_type]:
            pool_value = getattr(self, f"{instance.class_type}_{property}")
            match_type = getattr(self, f"{instance.class_type}_{property}_match")
            if not pool_value and match_type != "empty":
                continue
            value = str(getattr(instance, property))
            match = (
                match_type == "inclusion"
                and pool_value in value
                or match_type == "equality"
                and pool_value == value
                or match_type == "empty"
                and not value
                or bool(search(pool_value, value))
            )
            result = match != getattr(self, f"{instance.class_type}_{property}_invert")
            match_list.append(result)
        return match_list and all(match_list)

    def compute_pool(self):
        for model in self.models:
            if not self.manually_defined:
                kwargs = {"bulk": "object", "rbac": None, "form": {}}
                for property in vs.properties["filtering"][model]:
                    value = getattr(self, f"{model}_{property}")
                    match_type = getattr(self, f"{model}_{property}_match")
                    invert_type = getattr(self, f"{model}_{property}_invert")
                    if not value and match_type != "empty":
                        continue
                    kwargs["form"].update(
                        {
                            property: value,
                            f"{property}_filter": match_type,
                            f"{property}_invert": invert_type,
                        }
                    )
                if kwargs["form"]:
                    instances = controller.filtering(model, **kwargs)
                else:
                    instances = []
                setattr(self, f"{model}s", instances)
            else:
                instances = getattr(self, f"{model}s")
            setattr(self, f"{model}_number", len(instances))

    @classmethod
    def rbac_filter(cls, query, *_):
        return query.filter(cls.admin_only == false())


class Session(AbstractBase):

    __tablename__ = type = "session"
    private = True
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    timestamp = db.Column(db.TinyString)
    user = db.Column(db.SmallString)
    content = db.Column(db.LargeString, info={"log_change": False})
    device_id = db.Column(Integer, ForeignKey("device.id"))
    device = relationship(
        "Device", back_populates="sessions", foreign_keys="Session.device_id"
    )
    device_name = association_proxy("device", "name")


class ViewObject(AbstractBase):

    __tablename__ = export_type = "view_object"
    type = db.Column(db.SmallString)
    __mapper_args__ = {"polymorphic_identity": "view_object", "polymorphic_on": type}
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    view_id = db.Column(Integer, ForeignKey("view_object.id", ondelete="cascade"))
    view = relationship(
        "View", remote_side=[id], foreign_keys=view_id, back_populates="objects"
    )
    position_x = db.Column(Float, default=0.0)
    position_y = db.Column(Float, default=0.0)
    position_z = db.Column(Float, default=0.0)
    scale_x = db.Column(Float, default=1.0)
    scale_y = db.Column(Float, default=1.0)
    scale_z = db.Column(Float, default=1.0)
    rotation_x = db.Column(Float, default=0.0)
    rotation_y = db.Column(Float, default=0.0)
    rotation_z = db.Column(Float, default=0.0)

    def update(self, **kwargs):
        super().update(**kwargs)
        if "name" in kwargs:
            prefix = f"[{self.view}] " if self.view else ""
            self.name = f"{prefix}{kwargs['name']}"
        else:
            self.name = vs.get_time()


class Node(ViewObject):

    __tablename__ = class_type = "node"
    __mapper_args__ = {"polymorphic_identity": "node"}
    parent_type = "view_object"
    id = db.Column(Integer, ForeignKey(ViewObject.id), primary_key=True)
    model = db.Column(db.SmallString)
    device_id = db.Column(Integer, ForeignKey("device.id"))
    device = relationship("Device", foreign_keys="Node.device_id")
    device_name = association_proxy("device", "name")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.name:
            self.name = vs.get_time()


class Line(ViewObject):

    __tablename__ = class_type = "line"
    __mapper_args__ = {"polymorphic_identity": "line"}
    parent_type = "view_object"
    id = db.Column(Integer, ForeignKey(ViewObject.id), primary_key=True)
    link_id = db.Column(Integer, ForeignKey("link.id"))
    link = relationship("Link", foreign_keys="Line.link_id")
    link_name = association_proxy("link", "name")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.name:
            self.name = vs.get_time()


class Plan(ViewObject):

    __tablename__ = class_type = "plan"
    __mapper_args__ = {"polymorphic_identity": "plan"}
    parent_type = "view_object"
    id = db.Column(Integer, ForeignKey(ViewObject.id), primary_key=True)


class Label(ViewObject):

    __tablename__ = class_type = "label"
    __mapper_args__ = {"polymorphic_identity": "label"}
    parent_type = "view_object"
    id = db.Column(Integer, ForeignKey(ViewObject.id), primary_key=True)
    text = db.Column(db.SmallString)


class View(ViewObject):

    __tablename__ = class_type = "view"
    __mapper_args__ = {"polymorphic_identity": "view"}
    parent_type = "view_object"
    id = db.Column(Integer, ForeignKey(ViewObject.id), primary_key=True)
    last_modified = db.Column(db.TinyString, info={"log_change": False})
    objects = relationship("ViewObject", foreign_keys="ViewObject.view_id")

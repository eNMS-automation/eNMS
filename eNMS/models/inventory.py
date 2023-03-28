from re import search, sub
from sqlalchemy import and_, Boolean, event, ForeignKey, Integer, or_
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import backref, deferred, relationship
from sqlalchemy.schema import UniqueConstraint

from eNMS.controller import controller
from eNMS.models.base import AbstractBase
from eNMS.database import db
from eNMS.variables import vs


class Object(AbstractBase):
    __tablename__ = "object"
    type = db.Column(db.SmallString)
    __mapper_args__ = {"polymorphic_identity": "object", "polymorphic_on": type}
    id = db.Column(Integer, primary_key=True)
    creator = db.Column(db.SmallString)
    last_modified = db.Column(db.TinyString, info={"log_change": False})
    last_modified_by = db.Column(db.SmallString, info={"log_change": False})
    subtype = db.Column(db.SmallString)
    description = db.Column(db.LargeString)
    model = db.Column(db.SmallString)
    location = db.Column(db.SmallString)
    vendor = db.Column(db.SmallString)

    def update(self, **kwargs):
        super().update(**kwargs)
        if not hasattr(self, "class_type") or self.class_type == "network":
            return
        self.update_last_modified_properties()

    def delete(self):
        number = f"{self.class_type}_number"
        if self.class_type == "network":
            return
        for pool in self.pools:
            setattr(pool, number, getattr(pool, number) - 1)


class Node(Object):
    __tablename__ = "node"
    __mapper_args__ = {"polymorphic_identity": "node"}
    parent_type = "object"
    id = db.Column(Integer, ForeignKey(Object.id), primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    positions = db.Column(db.Dict, info={"log_change": False})
    latitude = db.Column(db.TinyString, default="0.0")
    longitude = db.Column(db.TinyString, default="0.0")
    networks = relationship(
        "Network", secondary=db.node_network_table, back_populates="nodes"
    )

    def post_update(self):
        return self.to_dict(include=["networks", "nodes"])

    def update(self, **kwargs):
        if self.positions and "positions" in kwargs:
            kwargs["positions"] = {**self.positions, **kwargs["positions"]}
        super().update(**kwargs)


class Device(Node):
    __tablename__ = class_type = export_type = "device"
    __mapper_args__ = {"polymorphic_identity": "device"}
    pretty_name = "Device"
    parent_type = "node"
    id = db.Column(Integer, ForeignKey(Node.id), primary_key=True)
    icon = db.Column(db.TinyString, default="router")
    operating_system = db.Column(db.SmallString)
    os_version = db.Column(db.SmallString)
    ip_address = db.Column(db.TinyString)
    port = db.Column(Integer, default=22)
    netmiko_driver = db.Column(db.TinyString, default="cisco_ios")
    napalm_driver = db.Column(db.TinyString, default="ios")
    scrapli_driver = db.Column(db.TinyString, default="cisco_iosxe")
    netconf_driver = db.Column(db.TinyString, default="default")
    configuration = deferred(db.Column(db.LargeString, info={"log_change": False}))
    operational_data = deferred(db.Column(db.LargeString, info={"log_change": False}))
    specialized_data = deferred(db.Column(db.LargeString, info={"log_change": False}))
    gateways = relationship(
        "Gateway", secondary=db.device_gateway_table, back_populates="devices"
    )
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
                for index, line in enumerate(content):
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
    __tablename__ = class_type = export_type = "link"
    __mapper_args__ = {"polymorphic_identity": "link"}
    pretty_name = "Link"
    parent_type = "object"
    id = db.Column(Integer, ForeignKey("object.id"), primary_key=True)
    name = db.Column(db.SmallString, unique=True)
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
    networks = relationship(
        "Network", secondary=db.link_network_table, back_populates="links"
    )
    __table_args__ = (UniqueConstraint(name, source_id, destination_id),)

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
    __tablename__ = type = class_type = "pool"
    models = ("device", "link")
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    manually_defined = db.Column(Boolean, default=False)
    creator = db.Column(db.SmallString)
    admin_only = db.Column(Boolean, default=False)
    last_modified = db.Column(db.TinyString, info={"log_change": False})
    last_modified_by = db.Column(db.SmallString, info={"log_change": False})
    description = db.Column(db.LargeString)
    target_services = relationship(
        "Service", secondary=db.service_target_pool_table, back_populates="target_pools"
    )
    runs = relationship(
        "Run", secondary=db.run_pool_table, back_populates="target_pools"
    )
    tasks = relationship("Task", secondary=db.task_pool_table, back_populates="pools")
    credential_devices = relationship(
        "Credential",
        secondary=db.credential_device_table,
        back_populates="device_pools",
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
        for property in vs.rbac["rbac_models"]["device"]:
            setattr(
                cls,
                f"rbac_group_{property}",
                relationship(
                    "Group",
                    secondary=getattr(db, f"pool_group_{property}_table"),
                    back_populates=f"rbac_pool_{property}",
                ),
            )

    def post_update(self):
        self.compute_pool()
        return super().post_update()

    def update(self, **kwargs):
        super().update(**kwargs)
        if not kwargs.get("migration_import"):
            self.update_last_modified_properties()

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
                    instances = controller.filtering(model, properties=["id"], **kwargs)
                else:
                    instances = []
                table = getattr(db, f"pool_{model}_table")
                db.session.execute(table.delete().where(table.c.pool_id == self.id))
                if instances:
                    values = [
                        {"pool_id": self.id, f"{model}_id": instance.id}
                        for instance in instances
                    ]
                    db.session.execute(table.insert().values(values))
            else:
                instances = getattr(self, f"{model}s")
            setattr(self, f"{model}_number", len(instances))


class Session(AbstractBase):
    __tablename__ = type = "session"
    private = True
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    timestamp = db.Column(db.TinyString)
    user = db.Column(db.SmallString)
    content = deferred(db.Column(db.LargeString, info={"log_change": False}))
    device_id = db.Column(Integer, ForeignKey("device.id"))
    device = relationship(
        "Device", back_populates="sessions", foreign_keys="Session.device_id"
    )
    device_name = association_proxy("device", "name")

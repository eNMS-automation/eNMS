from itertools import batched
from sqlalchemy import and_, Boolean, event, ForeignKey, Integer, or_
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import backref, deferred, relationship
from sqlalchemy.schema import UniqueConstraint

from eNMS.controller import controller
from eNMS.database import db
from eNMS.models.base import AbstractBase
from eNMS.variables import vs


class Object(AbstractBase):
    __tablename__ = "object"
    type = db.Column(db.SmallString)
    __mapper_args__ = {"polymorphic_identity": "object", "polymorphic_on": type}
    id = db.Column(Integer, primary_key=True)
    persistent_id = db.Column(db.TinyString)
    creator = db.Column(db.SmallString)
    creation_time = db.Column(db.TinyString)
    last_modified = db.Column(db.TinyString, info={"log_change": False})
    last_modified_by = db.Column(db.SmallString, info={"log_change": False})
    subtype = db.Column(db.SmallString)
    description = db.Column(db.LargeString)
    model = db.Column(db.SmallString)
    location = db.Column(db.SmallString)
    vendor = db.Column(db.SmallString)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.persistent_id:
            self.persistent_id = vs.get_persistent_id()

    @property
    def base_properties(self):
        return {**super().base_properties, "persistent_id": self.persistent_id}

    def delete(self):
        number = f"{self.class_type}_number"
        if self.class_type == "network":
            return
        for pool in self.pools:
            setattr(pool, number, getattr(pool, number) - 1)

    def update(self, **kwargs):
        super().update(**kwargs)
        if not hasattr(self, "class_type") or self.class_type == "network":
            return


class Device(Object):
    __tablename__ = class_type = export_type = "device"
    __mapper_args__ = {"polymorphic_identity": "device"}
    parent_type = "object"
    id = db.Column(Integer, ForeignKey(Object.id), primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    latitude = db.Column(db.TinyString, default="0.0")
    longitude = db.Column(db.TinyString, default="0.0")
    icon = db.Column(db.TinyString, default="router")
    operating_system = db.Column(db.SmallString)
    os_version = db.Column(db.SmallString)
    ip_address = db.Column(db.TinyString, index=True)
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
    networks = relationship(
        "Network", secondary=db.device_network_table, back_populates="devices"
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
    logs = relationship("Changelog", back_populates="device")

    def __repr__(self):
        return f"{self.name} ({self.model})" if self.model else str(self.name)

    @classmethod
    def database_init(cls):
        for property in vs.configuration_properties:
            for timestamp in vs.timestamps:
                column = db.Column(
                    db.SmallString, default="Never", info={"log_change": False}
                )
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
            db.query("link", rbac=None)
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
        properties = super().table_properties(**kwargs)
        search_properties = super().table_search(vs.configuration_properties, **kwargs)
        return {**properties, **search_properties}

    @property
    def ui_name(self):
        return f"{self.name} ({self.model})" if self.model else str(self.name)

    def update(self, **kwargs):
        old_name = self.name
        super().update(**kwargs)
        if not kwargs.get("migration_import") and self.name != old_name:
            for network in self.networks:
                network.positions[self.name] = network.positions.pop(old_name, [0, 0])

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


class Link(Object):
    __tablename__ = class_type = export_type = "link"
    __mapper_args__ = {"polymorphic_identity": "link"}
    parent_type = "object"
    id = db.Column(Integer, ForeignKey("object.id"), primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    color = db.Column(db.TinyString, default="#000000")
    source_id = db.Column(
        Integer,
        ForeignKey("device.id", ondelete="SET NULL"),
        info={"log_change": False},
    )
    destination_id = db.Column(
        Integer,
        ForeignKey("device.id", ondelete="SET NULL"),
        info={"log_change": False},
    )
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
    logs = relationship("Changelog", back_populates="link")
    __table_args__ = (UniqueConstraint(name, source_id, destination_id),)

    def update(self, **kwargs):
        if "source_name" in kwargs:
            kwargs["source"] = db.fetch(
                "device", name=kwargs.pop("source_name"), rbac=kwargs.get("rbac")
            ).id
            kwargs["destination"] = db.fetch(
                "device", name=kwargs.pop("destination_name"), rbac=kwargs.get("rbac")
            ).id
        if "source" in kwargs and "destination" in kwargs:
            kwargs.update(
                {"source_id": kwargs["source"], "destination_id": kwargs["destination"]}
            )
        super().update(**kwargs)

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


class Pool(AbstractBase):
    __tablename__ = type = class_type = "pool"
    models = ("device", "link")
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    manually_defined = db.Column(Boolean, default=False)
    creator = db.Column(db.SmallString)
    creation_time = db.Column(db.TinyString)
    last_modified = db.Column(db.TinyString, info={"log_change": False})
    last_modified_by = db.Column(db.SmallString, info={"log_change": False})
    description = db.Column(db.LargeString)
    include_networks = db.Column(Boolean, default=False)
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
    logs = relationship("Changelog", back_populates="pool")

    def compute_pool(self, commit=False):
        def transaction():
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
                    fast_compute = vs.settings["pool"]["fast_compute"]
                    if kwargs["form"]:
                        if model == "device" and not self.include_networks:
                            kwargs["sql_contraints"] = [
                                vs.models["device"].type != "network"
                            ]
                        if fast_compute:
                            kwargs["properties"] = ["id"]
                        instances = controller.filtering(model, **kwargs)
                    else:
                        instances = []
                    if fast_compute:
                        table = getattr(db, f"pool_{model}_table")
                        db.session.execute(
                            table.delete().where(table.c.pool_id == self.id)
                        )
                        if instances:
                            values = [
                                {"pool_id": self.id, f"{model}_id": instance.id}
                                for instance in instances
                            ]
                            for batch in batched(
                                values, vs.database["transactions"]["batch_size"]
                            ):
                                db.session.execute(table.insert(), batch)
                    else:
                        setattr(self, f"{model}s", instances)
                else:
                    instances = getattr(self, f"{model}s")
                setattr(self, f"{model}_number", len(instances))

        if commit:
            db.try_commit(transaction)
        else:
            transaction()

    @classmethod
    def configure_events(cls):
        for model in cls.models:

            @event.listens_for(getattr(cls, f"{model}s"), "append")
            def append(target, value, _):
                number = getattr(target, f"{value.export_type}_number") or 0
                setattr(target, f"{value.export_type}_number", number + 1)

            @event.listens_for(getattr(cls, f"{model}s"), "remove")
            def remove(target, value, _):
                number = getattr(target, f"{value.export_type}_number")
                setattr(target, f"{value.export_type}_number", number - 1)

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
            setattr(
                cls,
                f"{model}_number",
                db.Column(Integer, default=0, info={"log_change": False}),
            )
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


class Session(AbstractBase):
    __tablename__ = type = class_type = "session"
    private = True
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    timestamp = db.Column(db.TinyString)
    username = db.Column(db.SmallString)
    content = deferred(db.Column(db.LargeString, info={"log_change": False}))
    device_id = db.Column(Integer, ForeignKey("device.id"))
    device = relationship(
        "Device", back_populates="sessions", foreign_keys="Session.device_id"
    )
    device_name = association_proxy("device", "name")
    server_id = db.Column(Integer, ForeignKey("server.id"))
    server = relationship(
        "Server", back_populates="sessions", foreign_keys="Session.server_id"
    )
    server_name = association_proxy("server", "name")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.owners = [db.fetch("user", name=self.username)]

    def table_properties(self, **kwargs):
        properties = super().table_properties(**kwargs)
        search_properties = super().table_search(("content",), **kwargs)
        return {**properties, **search_properties}

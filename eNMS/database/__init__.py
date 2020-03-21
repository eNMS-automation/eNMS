from ast import literal_eval
from json import loads
from sqlalchemy import (
    Boolean,
    Column,
    create_engine,
    event,
    ForeignKey,
    Float,
    inspect,
    Integer,
    PickleType,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.mysql.base import MSMediumBlob
from sqlalchemy.ext.associationproxy import ASSOCIATION_PROXY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.types import JSON
from sqlalchemy.orm.collections import InstrumentedList

from eNMS.models import model_properties, models, property_types, relationships
from eNMS.setup import settings


class Database:

    private_properties = [
        "password",
        "enable_password",
        "custom_password",
        "netbox_token",
        "librenms_token",
        "opennms_password",
    ]

    dont_migrate = {
        "device": [
            "id",
            "configuration",
            "operational_data",
            "services",
            "source",
            "destination",
            "pools",
        ],
        "link": ["id", "pools"],
        "pool": ["id", "services"],
        "service": [
            "id",
            "sources",
            "destinations",
            "status",
            "tasks",
            "workflows",
            "tasks",
            "edges",
        ],
        "task": [
            "id",
            "service_name",
            "next_run_time",
            "is_active",
            "time_before_next_run",
            "status",
        ],
        "user": ["id", "pools"],
        "workflow_edge": ["id", "source_id", "destination_id", "workflow_id"],
    }

    import_classes = [
        "user",
        "device",
        "link",
        "pool",
        "service",
        "workflow_edge",
        "task",
    ]

    dont_serialize = {"device": ["configuration", "operational_data"]}

    def __init__(self):
        self.database_url = settings["database"]["url"]
        self.dialect = self.database_url.split(":")[0]
        self.configure_columns()
        self.engine = self.configure_engine()
        self.session = scoped_session(sessionmaker(autoflush=False, bind=self.engine))
        self.base = declarative_base()
        self.configure_associations()
        self.configure_events()
        self.field_conversion = {
            "dict": self.dict_conversion,
            "float": float,
            "int": int,
            "integer": int,
            "json": loads,
            "list": str,
            "str": str,
            "date": str,
        }

    @staticmethod
    def dict_conversion(input):
        try:
            return literal_eval(input)
        except Exception:
            return loads(input)

    def configure_engine(self):
        engine_parameters = {
            "convert_unicode": True,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        }
        if self.dialect == "mysql":
            engine_parameters.update(
                {
                    "max_overflow": settings["database"]["max_overflow"],
                    "pool_size": settings["database"]["pool_size"],
                }
            )
        return create_engine(self.database_url, **engine_parameters)

    def configure_columns(self):
        class CustomPickleType(PickleType):
            if self.dialect == "mysql":
                impl = MSMediumBlob

        self.Dict = MutableDict.as_mutable(CustomPickleType)
        self.List = MutableList.as_mutable(CustomPickleType)
        self.LargeString = Text(settings["database"]["large_string_length"])
        self.SmallString = String(settings["database"]["small_string_length"])

        default_ctypes = {
            self.Dict: {},
            self.List: [],
            self.LargeString: "",
            self.SmallString: "",
            Text: "",
        }

        class CustomColumn(Column):
            def __init__(self, ctype, *args, **kwargs):
                if "default" not in kwargs and ctype in default_ctypes:
                    kwargs["default"] = default_ctypes[ctype]
                super().__init__(ctype, *args, **kwargs)

        self.Column = CustomColumn

    def configure_events(self):
        @event.listens_for(self.base, "mapper_configured", propagate=True)
        def model_inspection(mapper, model):
            name = model.__tablename__
            for col in inspect(model).columns:
                if not col.info.get("model_properties", True):
                    continue
                model_properties[name].append(col.key)
                if col.type == PickleType and isinstance(col.default.arg, list):
                    property_types[col.key] = "list"
                else:
                    column_type = {
                        Boolean: "bool",
                        Integer: "int",
                        Float: "float",
                        JSON: "dict",
                        PickleType: "dict",
                    }.get(type(col.type), "str")
                    if col.key not in property_types:
                        property_types[col.key] = column_type
            for descriptor in inspect(model).all_orm_descriptors:
                if descriptor.extension_type is ASSOCIATION_PROXY:
                    property = (
                        descriptor.info.get("name")
                        or f"{descriptor.target_collection}_{descriptor.value_attr}"
                    )
                    model_properties[name].append(property)
            if hasattr(model, "parent_type"):
                model_properties[name].extend(model_properties[model.parent_type])
            if "service" in name and name != "service":
                model_properties[name].extend(model_properties["service"])
            models.update({name: model, name.lower(): model})
            model_properties[name] = list(set(model_properties[name]))
            for relation in mapper.relationships:
                if getattr(relation.mapper.class_, "private", False):
                    continue
                property = str(relation).split(".")[1]
                relationships[name][property] = {
                    "model": relation.mapper.class_.__tablename__,
                    "list": relation.uselist,
                }

    def configure_application_events(self, app):
        @event.listens_for(self.base, "after_insert", propagate=True)
        def log_instance_creation(mapper, connection, target):
            if hasattr(target, "name"):
                app.log("info", f"CREATION: {target.type} '{target.name}'")

        @event.listens_for(self.base, "before_delete", propagate=True)
        def log_instance_deletion(mapper, connection, target):
            name = getattr(target, "name", target.id)
            app.log("info", f"DELETION: {target.type} '{name}'")

        @event.listens_for(self.base, "before_update", propagate=True)
        def log_instance_update(mapper, connection, target):
            state, changelog = inspect(target), []
            for attr in state.attrs:
                hist = state.get_history(attr.key, True)
                if (
                    getattr(target, "dont_track_changes", False)
                    or getattr(state.class_, attr.key).info.get("dont_track_changes")
                    or attr.key in self.private_properties
                    or not hist.has_changes()
                ):
                    continue
                change = f"{attr.key}: "
                if type(getattr(target, attr.key)) == InstrumentedList:
                    if hist.deleted:
                        change += f"DELETED: {hist.deleted}"
                    if hist.added:
                        change += f"{' / ' if hist.deleted else ''}ADDED: {hist.added}"
                else:
                    change += (
                        f"'{hist.deleted[0] if hist.deleted else None}' => "
                        f"'{hist.added[0] if hist.added else None}'"
                    )
                changelog.append(change)
            if changelog:
                name, changes = (
                    getattr(target, "name", target.id),
                    " | ".join(changelog),
                )
                app.log("info", f"UPDATE: {target.type} '{name}': ({changes})")

        if app.settings["vault"]["active"]:

            @event.listens_for(models["service"].name, "set", propagate=True)
            def vault_update(target, new_value, old_value, *_):
                path = f"secret/data/{target.type}/{old_value}/password"
                data = app.vault_client.read(path)
                if not data:
                    return
                app.vault_client.write(
                    f"secret/data/{target.type}/{new_value}/password",
                    data={"password": data["data"]["data"]["password"]},
                )

    def configure_associations(self):

        self.service_device_table = Table(
            "service_device_association",
            self.base.metadata,
            Column("device_id", Integer, ForeignKey("device.id")),
            Column("service_id", Integer, ForeignKey("service.id")),
        )

        self.service_pool_table = Table(
            "service_pool_association",
            self.base.metadata,
            Column("pool_id", Integer, ForeignKey("pool.id")),
            Column("service_id", Integer, ForeignKey("service.id")),
        )

        self.run_device_table = Table(
            "run_device_association",
            self.base.metadata,
            Column("device_id", Integer, ForeignKey("device.id")),
            Column("run_id", Integer, ForeignKey("run.id", ondelete="cascade")),
        )

        self.run_pool_table = Table(
            "run_pool_association",
            self.base.metadata,
            Column("pool_id", Integer, ForeignKey("pool.id")),
            Column("run_id", Integer, ForeignKey("run.id", ondelete="cascade")),
        )

        self.task_device_table = Table(
            "task_device_association",
            self.base.metadata,
            Column("device_id", Integer, ForeignKey("device.id")),
            Column("task_id", Integer, ForeignKey("task.id")),
        )

        self.task_pool_table = Table(
            "task_pool_association",
            self.base.metadata,
            Column("pool_id", Integer, ForeignKey("pool.id")),
            Column("task_id", Integer, ForeignKey("task.id")),
        )

        self.service_workflow_table = Table(
            "service_workflow_association",
            self.base.metadata,
            Column("service_id", Integer, ForeignKey("service.id")),
            Column("workflow_id", Integer, ForeignKey("workflow.id")),
        )

        self.pool_device_table = Table(
            "pool_device_association",
            self.base.metadata,
            Column("pool_id", Integer, ForeignKey("pool.id")),
            Column("device_id", Integer, ForeignKey("device.id")),
        )

        self.pool_link_table = Table(
            "pool_link_association",
            self.base.metadata,
            Column("pool_id", Integer, ForeignKey("pool.id")),
            Column("link_id", Integer, ForeignKey("link.id")),
        )


db = Database()

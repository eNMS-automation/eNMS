from sqlalchemy import Boolean, Column, create_engine, event, ForeignKey, Float, inspect, Integer, PickleType, Table
from sqlalchemy.ext.associationproxy import ASSOCIATION_PROXY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.types import JSON

from eNMS.models import model_properties, models, property_types, relationships
from eNMS.setup import settings

class Database:

    def __init__(self):
        self.database_url = settings["database"]["url"]
        self.dialect = self.database_url.split(":")[0]
        self.engine = self.configure_engine()
        self.session = Session = scoped_session(sessionmaker(autoflush=False, bind=self.engine))
        self.base = declarative_base()
        self.configure_associations()
        self.configure_events()

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

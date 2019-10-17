from sqlalchemy import Boolean, event, Float, inspect, Integer, PickleType
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.types import JSON

from eNMS.database import Base
from eNMS.database.functions import fetch_all
from eNMS.models import model_properties, models, property_types, relationships
from eNMS.properties import private_properties
from eNMS.properties.database import dont_track_changes


@event.listens_for(Base, "mapper_configured", propagate=True)
def model_inspection(mapper, cls):
    name = cls.__tablename__
    for col in cls.__table__.columns:
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
    if hasattr(cls, "parent_type"):
        model_properties[name].extend(model_properties[cls.parent_type])
    if "service" in name and name != "service":
        model_properties[name].extend(model_properties["service"])
    model = {name: cls, name.lower(): cls}
    models.update(model)
    for relation in mapper.relationships:
        if getattr(relation.mapper.class_, "private", False):
            continue
        property = str(relation).split(".")[1]
        relationships[name][property] = {
            "model": relation.mapper.class_.__tablename__,
            "list": relation.uselist,
        }


def configure_events(app):
    @event.listens_for(Base, "init", propagate=True)
    def log_instance_creation(target, args, kwargs):
        if "type" not in target.__dict__ or "log" in target.type:
            return
        if "name" not in kwargs:
            kwargs["name"] = target.build_name(kwargs["scoped_name"])
        app.log("info", f"CREATION: {target.__dict__['type']} '{kwargs['name']}'")

    @event.listens_for(Base, "before_delete", propagate=True)
    def log_instance_deletion(mapper, connection, target):
        name = getattr(target, "name", target.id)
        app.log("info", f"DELETION: {target.type} '{name}'")

    @event.listens_for(Base, "before_update", propagate=True)
    def log_instance_update(mapper, connection, target):
        state, changelog = inspect(target), []
        for attr in state.attrs:
            if attr.key in private_properties or attr.key in dont_track_changes:
                continue
            hist = state.get_history(attr.key, True)
            if not hist.has_changes():
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
            name, changes = getattr(target, "name", target.id), " | ".join(changelog)
            app.log("info", f"UPDATE: {target.type} '{name}': ({changes})")

    @event.listens_for(models["service"], "before_update", propagate=True)
    def update_service_name(mapper, connection, target):
        if len(target.workflows) > 1:
            target.shared = True
        target.name = target.build_name()

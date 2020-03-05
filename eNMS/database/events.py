from sqlalchemy import Boolean, event, Float, inspect, Integer, PickleType
from sqlalchemy.ext.associationproxy import ASSOCIATION_PROXY
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.types import JSON

from eNMS.database import Base
from eNMS.models import model_properties, models, property_types, relationships
from eNMS.database.properties import private_properties


@event.listens_for(Base, "mapper_configured", propagate=True)
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


def configure_events(app):
    @event.listens_for(Base, "after_insert", propagate=True)
    def log_instance_creation(mapper, connection, target):
        if hasattr(target, "name"):
            app.log("info", f"CREATION: {target.type} '{target.name}'")

    @event.listens_for(Base, "before_delete", propagate=True)
    def log_instance_deletion(mapper, connection, target):
        name = getattr(target, "name", target.id)
        app.log("info", f"DELETION: {target.type} '{name}'")

    @event.listens_for(Base, "before_update", propagate=True)
    def log_instance_update(mapper, connection, target):
        state, changelog = inspect(target), []
        for attr in state.attrs:
            hist = state.get_history(attr.key, True)
            if (
                getattr(target, "dont_track_changes", False)
                or getattr(state.class_, attr.key).info.get("dont_track_changes")
                or attr.key in private_properties
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
            name, changes = getattr(target, "name", target.id), " | ".join(changelog)
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

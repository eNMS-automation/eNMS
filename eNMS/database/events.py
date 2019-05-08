from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.orm import scoped_session, sessionmaker

from eNMS.controller import controller
from eNMS.models import model_properties, models, property_types, relationships


@event.listens_for(Base, "mapper_configured", propagate=True)
def model_inspection(mapper: Mapper, cls: DeclarativeMeta) -> None:
    for col in cls.__table__.columns:
        model_properties[cls.__tablename__].append(col.key)
        if col.type == PickleType and col.default.arg == []:
            property_types[col.key] = "list"
        else:
            column_type = {
                Boolean: "bool",
                Integer: "int",
                Float: "float",
                PickleType: "dict",
            }.get(type(col.type), "str")
            if col.key not in property_types:
                property_types[col.key] = column_type
    if hasattr(cls, "parent_cls"):
        model_properties[cls.__tablename__].extend(model_properties[cls.parent_cls])
    model = {cls.__tablename__: cls, cls.__tablename__.lower(): cls}
    models.update(model)
    for relation in mapper.relationships:
        property = str(relation).split(".")[1]
        relationships[cls.__tablename__][property] = {
            "model": relation.mapper.class_.__tablename__,
            "list": relation.uselist,
        }

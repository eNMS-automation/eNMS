from contextlib import contextmanager
from logging import info
from os import environ
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from typing import Any, Generator, List, Tuple

from eNMS.models import classes

engine = create_engine(
    "sqlite:///database.db?check_same_thread=False", convert_unicode=True
)

Session = scoped_session(
    sessionmaker(expire_on_commit=False, autoflush=False, bind=engine)
)

Base = declarative_base()

SMALL_STRING_LENGTH = int(environ.get("SMALL_STRING_LENGTH", 255))
LARGE_STRING_LENGTH = int(environ.get("LARGE_STRING_LENGTH", 2 ** 16))


from sqlalchemy import Boolean, Float, Integer, PickleType
from sqlalchemy.inspection import inspect
from eNMS.models import (
    cls_to_properties,
    classes,
    service_classes,
    property_types,
    relationships,
)


@event.listens_for(Base, "mapper_configured", propagate=True)
def model_inspection(mapper, cls):
    for col in cls.__table__.columns:
        cls_to_properties[cls.__tablename__].append(col.key)
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
        cls_to_properties[cls.__tablename__].extend(cls_to_properties[cls.parent_cls])
    model = {cls.__tablename__: cls, cls.__tablename__.lower(): cls}
    if classes.get("Service") and issubclass(cls, classes["Service"]):
        service_classes[cls.__tablename__] = cls
    classes.update(model)
    for relation in mapper.relationships:
        property = str(relation).split(".")[1]
        relationships[cls.__tablename__][property] = {
            "model": relation.mapper.class_.__tablename__,
            "list": relation.uselist,
        }
    print(classes)


def fetch(model: str, **kwargs: Any) -> Any:
    return Session.query(classes[model]).filter_by(**kwargs).first()


def fetch_all(model: str) -> Tuple[Any]:
    return Session.query(classes[model]).all()


def fetch_all_visible(model: str) -> List[Any]:
    return [
        instance for instance in Session.query(classes[model]).all() if instance.visible
    ]


def objectify(model: str, object_list: List[int]) -> List[Any]:
    return [fetch(model, id=object_id) for object_id in object_list]


def delete(model: str, **kwargs: Any) -> dict:
    instance = Session.query(classes[model]).filter_by(**kwargs).first()
    if hasattr(instance, "type") and instance.type == "Task":
        instance.delete_task()
    serialized_instance = instance.serialized
    Session.delete(instance)
    Session.commit()
    return serialized_instance


def delete_all(*models: str) -> None:
    for model in models:
        for instance in fetch_all(model):
            delete(model, id=instance.id)
    Session.commit()


def choices(model: str) -> List[Tuple[int, str]]:
    return [(instance.id, str(instance)) for instance in classes[model].visible()]


def export(model: str) -> List[dict]:
    return [instance.to_dict(export=True) for instance in classes[model].visible()]


def get_one(model: str) -> Any:
    return Session.query(classes[model]).one_or_none()


def factory(cls_name: str, **kwargs: Any) -> Any:
    if "id" in kwargs:
        if kwargs["id"]:
            instance = fetch(cls_name, id=kwargs["id"])
        else:
            instance = kwargs.pop("id")
    else:
        instance = fetch(cls_name, name=kwargs["name"])
    if instance:
        instance.update(**kwargs)
    else:
        instance = classes[cls_name](**kwargs)
        Session.add(instance)
    Session.commit()
    return instance


@contextmanager
def session_scope() -> Generator:
    session = Session()  # type: ignore
    try:
        yield session
        session.commit()
    except Exception as e:
        info(str(e))
        session.rollback()
        raise e
    finally:
        session.close()

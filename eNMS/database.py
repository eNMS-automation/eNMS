from contextlib import contextmanager
from logging import info
from os import environ
from sqlalchemy import Boolean, create_engine, event, Float, Integer, PickleType
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.mapper import Mapper
from typing import Any, Generator, List, Tuple

from eNMS.models import model_properties, models, property_types, relationships

engine = create_engine(
    "sqlite:///database.db?check_same_thread=False", convert_unicode=True
)

Session = scoped_session(
    sessionmaker(expire_on_commit=False, autoflush=False, bind=engine)
)

Base = declarative_base()

SMALL_STRING_LENGTH = int(environ.get("SMALL_STRING_LENGTH", 255))
LARGE_STRING_LENGTH = int(environ.get("LARGE_STRING_LENGTH", 2 ** 16))


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


def fetch(model: str, **kwargs: Any) -> Any:
    return Session.query(models[model]).filter_by(**kwargs).first()


def fetch_all(model: str) -> Tuple[Any]:
    return Session.query(models[model]).all()


def fetch_all_visible(model: str) -> List[Any]:
    return [
        instance for instance in Session.query(models[model]).all() if instance.visible
    ]


def objectify(model: str, object_list: List[int]) -> List[Any]:
    return [fetch(model, id=object_id) for object_id in object_list]


def delete(model: str, **kwargs: Any) -> dict:
    instance = Session.query(models[model]).filter_by(**kwargs).first()
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
    return [(instance.id, str(instance)) for instance in models[model].visible()]


def export(model: str) -> List[dict]:
    return [instance.to_dict(export=True) for instance in models[model].visible()]


def get_one(model: str) -> Any:
    return Session.query(models[model]).one_or_none()


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
        instance = models[cls_name](**kwargs)
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

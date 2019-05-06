from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.model import DefaultMeta, Model
from os import environ
from sqlalchemy import exc
from sqlalchemy.ext.declarative import declarative_base
from typing import Any, Callable, List, Tuple

from eNMS.models import classes, cls_to_properties, property_types, service_classes

SMALL_STRING_LENGTH = int(environ.get("SMALL_STRING_LENGTH", 255))
LARGE_STRING_LENGTH = int(environ.get("LARGE_STRING_LENGTH", 2 ** 16))


class CustomMeta(DefaultMeta):
    def __init__(cls, name, bases, d):
        if hasattr(cls, "__table__"):
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
                cls_to_properties[cls.__tablename__].extend(
                    cls_to_properties[cls.parent_cls]
                )
            model = {cls.__tablename__: cls, cls.__tablename__.lower(): cls}
            if classes.get("Service") and issubclass(cls, classes["Service"]):
                service_classes[cls.__tablename__] = cls
            classes.update(model)
        super(CustomMeta, cls).__init__(name, bases, d)


db = SQLAlchemy(
    model_class=declarative_base(cls=Model, metaclass=CustomMeta, name="Model"),
    session_options={"expire_on_commit": False, "autoflush": False},
)


def fetch(model: str, **kwargs: Any) -> db.Model:
    return db.session.query(classes[model]).filter_by(**kwargs).first()


def fetch_all(model: str) -> Tuple[db.Model]:
    return classes[model].query.all()


def fetch_all_visible(model: str) -> List[db.Model]:
    return [instance for instance in classes[model].query.all() if instance.visible]


def objectify(model: str, object_list: List[int]) -> List[db.Model]:
    return [fetch(model, id=object_id) for object_id in object_list]


def delete(model: str, **kwargs: Any) -> dict:
    instance = db.session.query(classes[model]).filter_by(**kwargs).first()
    if hasattr(instance, "type") and instance.type == "Task":
        instance.delete_task()
    serialized_instance = instance.serialized
    db.session.delete(instance)
    db.session.commit()
    return serialized_instance


def delete_all(*models: str) -> None:
    for model in models:
        for instance in fetch_all(model):
            delete(model, id=instance.id)
    db.session.commit()


def choices(model: str) -> List[Tuple[int, str]]:
    return [(instance.id, str(instance)) for instance in classes[model].visible()]


def export(model: str) -> List[dict]:
    return [instance.to_dict(export=True) for instance in classes[model].visible()]


def get_one(model: str) -> db.Model:
    return classes[model].query.one()


def factory(cls_name: str, **kwargs: Any) -> db.Model:
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
        db.session.add(instance)
    db.session.commit()
    return instance


def integrity_rollback(function: Callable) -> Callable:
    def wrapper(*a: Any, **kw: Any) -> None:
        try:
            function(*a, **kw)
        except (exc.IntegrityError, exc.InvalidRequestError):
            db.session.rollback()

    return wrapper

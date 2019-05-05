from os import environ
from sqlalchemy import exc
from typing import Any, Callable, List, Tuple

from eNMS.modules import db
from eNMS.models import classes

SMALL_STRING_LENGTH = int(environ.get("SMALL_STRING_LENGTH", 255))
LARGE_STRING_LENGTH = int(environ.get("LARGE_STRING_LENGTH", 2 ** 16))


def fetch(model: str, **kwargs: Any) -> db.Model:
    print(kwargs)
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

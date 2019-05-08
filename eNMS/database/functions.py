from contextlib import contextmanager
from flask_login import current_user
from logging import info
from typing import Any, Generator, List, Tuple

from eNMS.database import Session
from eNMS.models import models


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


def factory(cls_name: str, commit=True, **kwargs: Any) -> Any:
    instance_id = kwargs.pop("id", 0)
    if instance_id:
        instance = fetch(cls_name, id=instance_id)
    else:
        instance = fetch(cls_name, name=kwargs["name"])
    if instance:
        instance.update(**kwargs)
    else:
        instance = models[cls_name](**kwargs)
        Session.add(instance)
    if commit:
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

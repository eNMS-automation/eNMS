from contextlib import contextmanager
from logging import info
from os import environ
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from typing import Any, Callable, Generator, List, Tuple

from eNMS.models import classes, cls_to_properties, property_types, service_classes

SMALL_STRING_LENGTH = int(environ.get("SMALL_STRING_LENGTH", 255))
LARGE_STRING_LENGTH = int(environ.get("LARGE_STRING_LENGTH", 2 ** 16))

engine = create_engine(
    "sqlite:///database.db?check_same_thread=False", convert_unicode=True
)

Session = scoped_session(
    sessionmaker(expire_on_commit=False, autoflush=False, bind=engine)
)
SQLBase = declarative_base()
SQLBase.query = Session.query_property()
SQLBase.metadata.create_all(bind=engine)


def fetch(model: str, **kwargs: Any) -> SQLBase:
    with session_scope() as session:
        return session.query(classes[model]).filter_by(**kwargs).first()


def fetch_all(model: str) -> Tuple[SQLBase]:
    return classes[model].query.all()


def fetch_all_visible(model: str) -> List[SQLBase]:
    return [instance for instance in classes[model].query.all() if instance.visible]


def objectify(model: str, object_list: List[int]) -> List[SQLBase]:
    return [fetch(model, id=object_id) for object_id in object_list]


def delete(model: str, **kwargs: Any) -> dict:
    instance = session.query(classes[model]).filter_by(**kwargs).first()
    if hasattr(instance, "type") and instance.type == "Task":
        instance.delete_task()
    serialized_instance = instance.serialized
    session.delete(instance)
    session.commit()
    return serialized_instance


def delete_all(*models: str) -> None:
    for model in models:
        for instance in fetch_all(model):
            delete(model, id=instance.id)
    session.commit()


def choices(model: str) -> List[Tuple[int, str]]:
    return [(instance.id, str(instance)) for instance in classes[model].visible()]


def export(model: str) -> List[dict]:
    return [instance.to_dict(export=True) for instance in classes[model].visible()]


def get_one(model: str) -> SQLBase:
    return classes[model].query.one()


def factory(cls_name: str, **kwargs: Any) -> SQLBase:
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
        session.add(instance)
    session.commit()
    return instance


def integrity_rollback(function: Callable) -> Callable:
    def wrapper(*a: Any, **kw: Any) -> None:
        try:
            function(*a, **kw)
        except (exc.IntegrityError, exc.InvalidRequestError):
            session.rollback()

    return wrapper


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

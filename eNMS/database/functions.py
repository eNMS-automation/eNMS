from contextlib import contextmanager
from logging import info
from re import search
from sqlalchemy import func
from typing import Any, Generator, List, Tuple

from eNMS.database import Session, session_factory
from eNMS.models import models, relationships


def fetch(
    model: str,
    allow_none: Any = False,
    session: Any = None,
    all_matches: Any = False,
    **kwargs: Any,
) -> Any:
    sess = session or Session
    query = sess.query(models[model]).filter_by(**kwargs)
    result = query.all() if all_matches else query.first()
    if result or allow_none:
        return result
    else:
        raise Exception(
            f"There is no {model} in the database "
            f"with the following characteristics: {kwargs}"
        )


def fetch_all(model: str) -> Tuple[Any]:
    return Session.query(models[model]).all()


def count(model: str, **kwargs: Any) -> Tuple[Any]:
    return Session.query(func.count(models[model].id)).filter_by(**kwargs).scalar()


def get_query_count(query: Any) -> int:
    count_query = query.statement.with_only_columns([func.count()]).order_by(None)
    return query.session.execute(count_query).scalar()


def get_relationship_count(obj: Any, relation: str) -> int:
    related_model = models[relationships[obj.type][relation]["model"]]
    return Session.query(func.count(related_model.id)).with_parent(obj).scalar()


def objectify(model: str, object_list: List[int]) -> List[Any]:
    return [fetch(model, id=object_id) for object_id in object_list]


def convert_value(model: str, attr: str, value: str, value_type: str) -> Any:
    relation = relationships[model].get(attr)
    if not relation:
        return value
    if relation["list"]:
        return [fetch(relation["model"], **{value_type: v}) for v in value]
    else:
        return fetch(relation["model"], **{value_type: value})


def delete(model: str, allow_none: Any = False, **kwargs: Any) -> Any:
    instance = Session.query(models[model]).filter_by(**kwargs).first()
    if allow_none and not instance:
        return None
    if hasattr(instance, "type") and instance.type == "Task":
        instance.delete_task()
    serialized_instance = instance.serialized
    Session.delete(instance)
    return serialized_instance


def delete_all(*models: str) -> None:
    for model in models:
        for instance in fetch_all(model):
            delete(model, id=instance.id)


def choices(model: str) -> List[Tuple[int, str]]:
    return [(instance.id, str(instance)) for instance in models[model].visible()]


def export(model: str) -> List[dict]:
    return [instance.to_dict(export=True) for instance in models[model].visible()]


def factory(cls_name: str, **kwargs: Any) -> Any:
    if "/" in kwargs.get("name", ""):
        raise Exception("Names cannot contain a slash ('/').")
    instance, instance_id = None, kwargs.pop("id", 0)
    if instance_id:
        instance = fetch(cls_name, id=instance_id)
    elif "name" in kwargs:
        instance = fetch(cls_name, allow_none=True, name=kwargs["name"])
    if instance:
        if kwargs.get("must_be_new"):
            raise Exception(f"There already is a {cls_name} with the same name.")
        else:
            instance.update(**kwargs)
    else:
        instance = models[cls_name](**kwargs)
        Session.add(instance)
    return instance


def handle_exception(exc: str) -> str:
    match = search("UNIQUE constraint failed: (\w+).(\w+)", exc)
    if match:
        return f"There already is a {match.group(1)} with the same {match.group(2)}."
    else:
        return exc


@contextmanager
def session_scope() -> Generator:
    session = session_factory()[1]()  # type: ignore
    try:
        yield session
        session.commit()
    except Exception as e:
        info(str(e))
        session.rollback()
        raise e
    finally:
        session.close()

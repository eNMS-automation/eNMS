from re import search
from sqlalchemy import Boolean, Float, func, Integer

from eNMS.setup import properties
from eNMS.database import Session
from eNMS.database.dialect import Column, LargeString
from eNMS.models import models


def fetch(model, allow_none=False, all_matches=False, **kwargs):
    query = Session.query(models[model]).filter_by(**kwargs)
    result = query.all() if all_matches else query.first()
    if result or allow_none:
        return result
    else:
        raise Exception(
            f"There is no {model} in the database "
            f"with the following characteristics: {kwargs}"
        )


def fetch_all(model, **kwargs):
    return fetch(model, allow_none=True, all_matches=True, **kwargs)


def count(model, **kwargs):
    return Session.query(func.count(models[model].id)).filter_by(**kwargs).scalar()


def get_query_count(query):
    count_query = query.statement.with_only_columns([func.count()]).order_by(None)
    return query.session.execute(count_query).scalar()


def objectify(model, object_list):
    return [fetch(model, id=object_id) for object_id in object_list]


def delete(model, allow_none=False, **kwargs):
    instance = Session.query(models[model]).filter_by(**kwargs).first()
    if allow_none and not instance:
        return None
    instance.delete()
    serialized_instance = instance.serialized
    Session.delete(instance)
    return serialized_instance


def delete_all(*models):
    for model in models:
        for instance in fetch_all(model):
            delete(model, id=instance.id)


def export(model):
    return [instance.to_dict(export=True) for instance in fetch_all(model)]


def factory(cls_name, **kwargs):
    if set("/\\'" + '"') & set(kwargs.get("name", "") + kwargs.get("scoped_name", "")):
        raise Exception("Names cannot contain a slash or a quote.")
    instance, instance_id = None, kwargs.pop("id", 0)
    if instance_id:
        instance = fetch(cls_name, id=instance_id)
    elif "name" in kwargs:
        instance = fetch(cls_name, allow_none=True, name=kwargs["name"])
    if instance and not kwargs.get("must_be_new"):
        instance.update(**kwargs)
    else:
        instance = models[cls_name](**kwargs)
        Session.add(instance)
    return instance


def handle_exception(exc):
    match = search("UNIQUE constraint failed: (\w+).(\w+)", exc)
    if match:
        return f"There already is a {match.group(1)} with the same {match.group(2)}."
    else:
        return exc


def set_custom_properties(cls):
    for property, values in properties["custom"].get(cls.__tablename__, {}).items():
        setattr(
            cls,
            property,
            Column(
                {
                    "boolean": Boolean,
                    "float": Float,
                    "integer": Integer,
                    "string": LargeString,
                }[values["type"]],
                default=values["default"],
            ),
        )
    return cls

from re import search
from sqlalchemy import func

from eNMS.database import Session
from eNMS.models import models, relationships


def fetch(
    model, allow_none=False, all_matches=False, **kwargs
):
    query = Session.query(models[model]).filter_by(**kwargs)
    result = query.all() if all_matches else query.first()
    if result or allow_none:
        return result
    else:
        raise Exception(
            f"There is no {model} in the database "
            f"with the following characteristics: {kwargs}"
        )


def fetch_all(model):
    return Session.query(models[model]).all()


def count(model, **kwargs):
    return Session.query(func.count(models[model].id)).filter_by(**kwargs).scalar()


def get_query_count(query):
    count_query = query.statement.with_only_columns([func.count()]).order_by(None)
    return query.session.execute(count_query).scalar()


def get_relationship_count(obj, relation):
    related_model = models[relationships[obj.type][relation]["model"]]
    return Session.query(func.count(related_model.id)).with_parent(obj).scalar()


def objectify(model, object_list):
    return [fetch(model, id=object_id) for object_id in object_list]


def convert_value(model, attr, value, value_type):
    relation = relationships[model].get(attr)
    if not relation:
        return value
    if relation["list"]:
        return [fetch(relation["model"], **{value_type: v}) for v in value]
    else:
        return fetch(relation["model"], **{value_type: value})


def delete(model, allow_none=False, **kwargs):
    instance = Session.query(models[model]).filter_by(**kwargs).first()
    if allow_none and not instance:
        return None
    if hasattr(instance, "type") and instance.type == "task":
        instance.delete_task()
    serialized_instance = instance.serialized
    Session.delete(instance)
    return serialized_instance


def delete_all(*models):
    for model in models:
        for instance in fetch_all(model):
            delete(model, id=instance.id)


def export(model):
    return [instance.to_dict(export=True) for instance in models[model].visible()]


def factory(cls_name, **kwargs):
    if {"/", '"', "'"} & set(kwargs.get("name", "")):
        raise Exception("Names cannot contain a slash or a quote.")
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


def handle_exception(exc):
    match = search("UNIQUE constraint failed: (\w+).(\w+)", exc)
    if match:
        return f"There already is a {match.group(1)} with the same {match.group(2)}."
    else:
        return exc

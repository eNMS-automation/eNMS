from flask_login import current_user as user
from json import dumps, loads
from sqlalchemy.ext.mutable import MutableDict, MutableList
from typing import Any, List, Tuple
from wtforms import SelectField, SelectMultipleField

from eNMS.extensions import db, USE_VAULT, vault_client
from eNMS.functions import fetch, objectify, choices
from eNMS.properties import (
    cls_to_properties,
    dont_migrate,
    property_types,
    boolean_properties,
    relationships as rel,
    private_properties,
)


class Base(db.Model):

    __abstract__ = True

    def __init__(self, **kwargs: Any) -> None:
        self.update(**kwargs)

    def __lt__(self, other: db.Model) -> bool:
        return True

    def __repr__(self) -> str:
        return self.name

    def __getattribute__(self, property: str) -> Any:
        if property in private_properties and USE_VAULT:
            path = f"secret/data/{self.__tablename__}/{self.name}/{property}"
            data = vault_client.read(path)
            return data["data"]["data"][property] if data else ""
        else:
            return super().__getattribute__(property)

    def __setattr__(self, property: str, value: Any) -> None:
        if property in private_properties and USE_VAULT:
            if not value:
                return
            vault_client.write(
                f"secret/data/{self.__tablename__}/{self.name}/{property}",
                data={property: value},
            )
        else:
            super().__setattr__(property, value)

    def update(self, **kwargs: Any) -> None:
        serial = rel.get(self.__tablename__, rel["Service"])
        for property, value in kwargs.items():
            property_type = property_types.get(property, None)
            if property in serial:
                value = fetch(serial[property], id=value)
            elif property[:-1] in serial:
                value = objectify(serial[property[:-1]], value)
            elif property in boolean_properties:
                value = kwargs[property] not in (None, False)
            elif "regex" in property:
                value = property in kwargs
            elif property_type == "dict" and type(value) == str:
                value = loads(value) if value else {}
            elif property_type in ["float", "int"]:
                default_value = getattr(self.__table__.c, property).default
                if default_value and not value:
                    value = default_value.arg
                value = {"float": float, "int": int}[property_type](value or 0)
            setattr(self, property, value)

    def get_properties(self) -> dict:
        result = {}
        for property in cls_to_properties[self.type]:
            if property in private_properties:
                continue
            try:
                dumps(getattr(self, property))
                result[property] = getattr(self, property)
            except TypeError:
                result[property] = str(getattr(self, property))
        return result

    def get_export_properties(self) -> dict:
        result = {}
        for property in cls_to_properties[self.type]:
            value = getattr(self, property)
            if not value or property in private_properties:
                continue
            try:
                dumps(value)
            except TypeError:
                continue
            if isinstance(value, MutableList):
                value = list(value)
            if isinstance(value, MutableDict):
                value = dict(value)
            result[property] = value
        return result

    def to_dict(self, export: bool = False) -> dict:
        properties = self.get_export_properties() if export else self.get_properties()
        no_migrate = dont_migrate.get(self.type, dont_migrate["Service"])
        for property in rel.get(self.type, rel["Service"]):
            if export and property in no_migrate:
                continue
            if hasattr(self, property):
                if hasattr(getattr(self, property), "get_properties"):
                    properties[property] = (
                        getattr(self, property).id
                        if export
                        else getattr(self, property).get_properties()
                    )
            if hasattr(self, f"{property}s"):
                # a workflow has edges: we need to know not only the edge
                # properties, but also the properties of its source and
                # destination: we need the serialized edge.
                properties[f"{property}s"] = [
                    obj.id if export else obj.get_properties()
                    for obj in getattr(self, f"{property}s")
                ]
        if export:
            for property in no_migrate:
                properties.pop(property, None)
        return properties

    @classmethod
    def visible(cls) -> List:
        if cls.__tablename__ == "Pool" and user.pools:
            return user.pools
        elif cls.__tablename__ in ("Device", "Link") and user.pools:
            objects: set = set()
            for pool in user.pools:
                objects |= set(getattr(pool, f"{cls.class_type}s"))
            return list(objects)
        else:
            return cls.query.all()

    @property
    def serialized(self) -> dict:
        return self.to_dict()

    @classmethod
    def export(cls: db.Model) -> List[dict]:
        return [obj.to_dict(export=True) for obj in cls.visible()]

    @classmethod
    def choices(cls: db.Model) -> List[Tuple[int, str]]:
        return [(obj.id, str(obj)) for obj in cls.visible()]

    @classmethod
    def serialize(cls: db.Model) -> List[dict]:
        return [obj.serialized for obj in cls.visible()]


class ObjectField(SelectField):
    def __init__(self, model: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.choices = choices(model)


class MultipleObjectField(SelectMultipleField):
    def __init__(self, model: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.choices = choices(model)

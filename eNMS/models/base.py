from flask_login import current_user as user
from sqlalchemy.ext.mutable import MutableDict, MutableList
from typing import Any, List

from eNMS.controller import controller
from eNMS.models import cls_to_properties, property_types, relationships
from eNMS.modules import db
from eNMS.database import fetch, objectify
from eNMS.properties import dont_migrate, private_properties


class Base(db.Model):

    __abstract__ = True

    def __init__(self, **kwargs: Any) -> None:
        self.update(**kwargs)

    def __lt__(self, other: db.Model) -> bool:
        return True

    def __repr__(self) -> str:
        return self.name

    def __getattribute__(self, property: str) -> Any:
        if property in private_properties and controller.USE_VAULT:
            path = f"secret/data/{self.__tablename__}/{self.name}/{property}"
            data = controller.vault_client.read(path)
            return data["data"]["data"][property] if data else ""
        else:
            return super().__getattribute__(property)

    def __setattr__(self, property: str, value: Any) -> None:
        if property in private_properties and controller.USE_VAULT:
            if not value:
                return
            controller.vault_client.write(
                f"secret/data/{self.__tablename__}/{self.name}/{property}",
                data={property: value},
            )
        else:
            super().__setattr__(property, value)

    def update(self, **kwargs: Any) -> None:
        relation = relationships[self.__tablename__]
        for property, value in kwargs.items():
            property_type = property_types.get(property, None)
            if property in relation:
                if relation[property]["list"]:
                    value = objectify(relation[property]["model"], value)
                else:
                    value = fetch(relation[property]["model"], id=value)
            if property_type == "bool":
                value = value not in (False, "false")
            setattr(self, property, value)

    def get_properties(self, export=False) -> dict:
        result = {}
        for property in cls_to_properties[self.type]:
            value = getattr(self, property)
            if property in private_properties:
                continue
            if export:
                if isinstance(value, MutableList):
                    value = list(value)
                if isinstance(value, MutableDict):
                    value = dict(value)
            result[property] = value
        return result

    def to_dict(self, export: bool = False) -> dict:
        properties = self.get_properties(export)
        no_migrate = dont_migrate.get(self.type, dont_migrate["Service"])
        for property, relation in relationships[self.type].items():
            value = getattr(self, property)
            if export and property in no_migrate:
                continue
            if relation["list"]:
                properties[property] = [
                    obj.id if export else obj.get_properties() for obj in value
                ]
            else:
                properties[property] = value.id if export else value.get_properties()
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

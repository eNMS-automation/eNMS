from sqlalchemy.ext.mutable import MutableDict, MutableList

from eNMS import app
from eNMS.database import Base
from eNMS.database.functions import factory, fetch, objectify
from eNMS.models import model_properties, property_types, relationships
from eNMS.properties import dont_serialize, private_properties
from eNMS.properties.database import dont_migrate


class AbstractBase(Base):

    __abstract__ = True

    def __init__(self, **kwargs):
        self.update(**kwargs)

    def __lt__(self, other):
        return True

    def __repr__(self):
        return self.name

    def __getattribute__(self, property):
        if property in private_properties and app.settings["vault"]["active"]:
            path = f"secret/data/{self.__tablename__}/{self.name}/{property}"
            data = app.vault_client.read(path)
            return data["data"]["data"][property] if data else ""
        else:
            return super().__getattribute__(property)

    def __setattr__(self, property, value):
        if property in private_properties:
            if not value:
                return
            if app.settings["vault"]["active"]:
                app.vault_client.write(
                    f"secret/data/{self.__tablename__}/{self.name}/{property}",
                    data={property: value},
                )
            else:
                super().__setattr__(property, value)
        else:
            super().__setattr__(property, value)

    @property
    def ui_name(self):
        return self.name

    def update(self, **kwargs):
        relation = relationships[self.__tablename__]
        for property, value in kwargs.items():
            if not hasattr(self, property):
                continue
            property_type = property_types.get(property, None)
            if property in relation:
                if relation[property]["list"]:
                    value = objectify(relation[property]["model"], value)
                else:
                    value = fetch(relation[property]["model"], id=value)
            if property_type == "bool":
                value = value not in (False, "false")
            setattr(self, property, value)

    def delete(self):
        pass

    def get_properties(self, export=False, exclude=None, include=None):
        result = {}
        no_migrate = dont_migrate.get(self.type, dont_migrate["service"])
        properties = list(model_properties[self.type])
        if not export:
            properties.extend(getattr(self, "model_properties", []))
        for property in properties:
            if not hasattr(self, property):
                continue
            if property in dont_serialize.get(self.type, []):
                continue
            if property in private_properties:
                continue
            if include and property not in include or exclude and property in exclude:
                continue
            if export and property in no_migrate:
                continue
            value = getattr(self, property)
            if export:
                if isinstance(value, MutableList):
                    value = list(value)
                if isinstance(value, MutableDict):
                    value = dict(value)
                if value is None:
                    continue
            result[property] = value
        return result

    def table_properties(self, **_):
        return self.get_properties()

    def duplicate(self, **kwargs):
        properties = {
            k: v for (k, v) in self.get_properties().items() if k not in ("id", "name")
        }
        instance = factory(self.type, **{**properties, **kwargs})
        return instance

    def to_dict(
        self, export=False, relation_names_only=False, exclude=None, include=None
    ):
        properties = self.get_properties(export, exclude=exclude)
        no_migrate = dont_migrate.get(self.type, dont_migrate["service"])
        for property, relation in relationships[self.type].items():
            if include and property not in include or exclude and property in exclude:
                continue
            if export and property in no_migrate:
                continue
            value = getattr(self, property)
            if relation["list"]:
                properties[property] = [
                    obj.name
                    if export or relation_names_only
                    else obj.get_properties(exclude=exclude)
                    for obj in value
                ]
            else:
                if not value:
                    continue
                properties[property] = (
                    value.name
                    if export or relation_names_only
                    else value.get_properties(exclude=exclude)
                )
        return properties

    @property
    def serialized(self):
        return self.to_dict()

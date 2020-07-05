from sqlalchemy.ext.mutable import MutableDict, MutableList

from eNMS import app
from eNMS.database import db
from eNMS.models import model_properties, property_types, relationships


class AbstractBase(db.base):

    __abstract__ = True
    model_properties = []

    def __init__(self, **kwargs):
        self.update(**kwargs)

    def __lt__(self, other):
        return True

    def __repr__(self):
        return getattr(self, "name", str(self.id))

    def __getattribute__(self, property):
        if property in db.private_properties:
            if app.use_vault:
                target = self.service if self.type == "run" else self
                path = f"secret/data/{target.type}/{target.name}/{property}"
                data = app.vault_client.read(path)
                value = data["data"]["data"][property] if data else ""
            else:
                value = super().__getattribute__(property)
            return value
        else:
            return super().__getattribute__(property)

    def __setattr__(self, property, value):
        if property in db.private_properties:
            if not value:
                return
            value = app.encrypt(str.encode(value))
            if app.use_vault:
                app.vault_client.write(
                    f"secret/data/{self.type}/{self.name}/{property}",
                    data={property: value.decode("utf-8")},
                )
            else:
                super().__setattr__(property, value)
        else:
            super().__setattr__(property, value)

    @classmethod
    def filtering_constraints(cls, **_):
        return []

    @property
    def ui_name(self):
        return self.name

    @property
    def base_properties(self):
        return {p: getattr(self, p) for p in ("id", "name", "type")}

    def update(self, **kwargs):
        relation = relationships[self.__tablename__]
        for property, value in kwargs.items():
            if not hasattr(self, property):
                continue
            property_type = property_types.get(property, None)
            if property in relation:
                if relation[property]["list"]:
                    value = db.objectify(relation[property]["model"], value)
                elif value:
                    value = db.fetch(relation[property]["model"], id=value)
            if property_type == "bool":
                value = value not in (False, "false")
            setattr(self, property, value)

    def delete(self):
        pass

    def get_properties(self, export=False, exclude=None, include=None):
        result = {}
        no_migrate = db.dont_migrate.get(self.type, db.dont_migrate["service"])
        properties = list(model_properties[self.type])
        for property in properties:
            if property in db.private_properties:
                continue
            if property in db.dont_serialize.get(self.type, []):
                continue
            if export and property in getattr(self, "model_properties", []):
                continue
            if include and property not in include or exclude and property in exclude:
                continue
            if export and property in no_migrate:
                continue
            try:
                value = getattr(self, property)
            except AttributeError:
                continue
            if export:
                if isinstance(value, MutableList):
                    value = list(value)
                if isinstance(value, MutableDict):
                    value = dict(value)
                if value is None:
                    continue
            result[property] = value
        return result

    @classmethod
    def rbac_filter(cls, query, mode, user):
        return query

    def table_properties(self, **kwargs):
        rest_api = kwargs.get("rest_api_request")
        columns = [c["data"] for c in kwargs["columns"]] if rest_api else None
        return self.get_properties(include=columns)

    def duplicate(self, **kwargs):
        properties = {
            k: v for (k, v) in self.get_properties().items() if k not in ("id", "name")
        }
        instance = db.factory(self.type, **{**properties, **kwargs})
        return instance

    def to_dict(
        self, export=False, relation_names_only=False, exclude=None, include=None
    ):
        properties = self.get_properties(export, exclude=exclude)
        no_migrate = db.dont_migrate.get(self.type, db.dont_migrate["service"])
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

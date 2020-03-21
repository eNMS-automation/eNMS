from eNMS import app
from eNMS.database import db
from eNMS.models import model_properties, property_types, relationships


class AbstractBase(db.base):

    __abstract__ = True

    def __init__(self, **kwargs):
        self.update(**kwargs)

    def __lt__(self, other):
        return True

    def __repr__(self):
        return self.name

    def __getattribute__(self, property):
        if property in db.private_properties and app.settings["vault"]["active"]:
            path = f"secret/data/{self.__tablename__}/{self.name}/{property}"
            data = app.vault_client.read(path)
            return data["data"]["data"][property] if data else ""
        else:
            return super().__getattribute__(property)

    def __setattr__(self, property, value):
        if property in db.private_properties:
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
                else:
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
        if not export:
            properties.extend(getattr(self, "model_properties", []))
        for property in properties:
            if not hasattr(self, property):
                continue
            if property in db.dont_serialize.get(self.type, []):
                continue
            if property in db.private_properties:
                continue
            if include and property not in include or exclude and property in exclude:
                continue
            if export and property in no_migrate:
                continue
            value = getattr(self, property)
            if export:
                if isinstance(value, db.List):
                    value = list(value)
                if isinstance(value, db.Dict):
                    value = dict(value)
                if value is None:
                    continue
            result[property] = value
        return result

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

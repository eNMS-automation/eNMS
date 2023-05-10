from collections import defaultdict
from flask_login import current_user
from sqlalchemy import or_
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.sql.expression import false

from eNMS.database import db
from eNMS.environment import env
from eNMS.variables import vs


class AbstractBase(db.base):
    __abstract__ = True
    model_properties = {}

    def __init__(self, **kwargs):
        self.update(**kwargs)
        self.update_rbac()

    def __lt__(self, other):
        return True

    def __repr__(self):
        return str(getattr(self, "name", self.id))

    def __getattribute__(self, property):
        if property in vs.private_properties_set:
            if env.use_vault:
                target = self.service if self.type == "run" else self
                path = f"secret/data/{target.type}/{target.name}/{property}"
                data = env.vault_client.read(path)
                value = data["data"]["data"][property] if data else ""
            else:
                value = super().__getattribute__(property)
            return value
        else:
            return super().__getattribute__(property)

    def __setattr__(self, property, value):
        if property in vs.private_properties_set:
            if not value:
                return
            value = env.encrypt_password(value).decode("utf-8")
            if env.use_vault:
                env.vault_client.write(
                    f"secret/data/{self.type}/{self.name}/{property}",
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
        return {prop: getattr(self, prop) for prop in ("id", "name", "type")}

    def post_update(self):
        return self.get_properties()

    def update(self, rbac="edit", **kwargs):
        self.filter_rbac_kwargs(kwargs)
        relation = vs.relationships[self.__tablename__]
        for property, value in kwargs.items():
            if not hasattr(self, property):
                continue
            property_type = vs.model_properties[self.__tablename__].get(property, None)
            if property in relation:
                if relation[property]["list"]:
                    value = db.objectify(relation[property]["model"], value)
                elif value:
                    value = db.fetch(relation[property]["model"], id=value, rbac="read")
            if property_type == "bool":
                value = value not in (False, "false")
            elif property_type == "dict":
                table_properties = vs.properties["custom"].get(self.__tablename__, {})
                if table_properties.get(property, {}).get("merge_update"):
                    current_value = getattr(self, property)
                    if current_value:
                        value = {**current_value, **value}
            setattr(self, property, value)
        if getattr(self, "class_type", None) not in vs.rbac["rbac_models"]:
            return
        for group in db.fetch_all("group", force_read_access=True, rbac=None):
            if group not in self.rbac_read:
                self.rbac_read.append(group)

    def update_last_modified_properties(self):
        self.last_modified = vs.get_time()
        self.last_modified_by = getattr(current_user, "name", "admin")

    def filter_rbac_kwargs(self, kwargs):
        if getattr(self, "class_type", None) not in vs.rbac["rbac_models"]:
            return
        rbac_properties = ["owners", "restrict_to_owners"]
        model_rbac_properties = list(vs.rbac["rbac_models"][self.class_type])
        is_admin = getattr(current_user, "is_admin", True)
        if not is_admin and current_user not in self.owners:
            for property in rbac_properties + model_rbac_properties:
                kwargs.pop(property, None)

    @classmethod
    def rbac_filter(cls, query, mode, user, join_class=None):
        model = join_class or getattr(cls, "class_type", None)
        if model not in vs.rbac["rbac_models"]:
            return query
        if join_class:
            query = query.join(getattr(cls, join_class))
        user_group = [group.id for group in user.groups]
        property = getattr(vs.models[model], f"rbac_{mode}")
        rbac_constraint = property.any(vs.models["group"].id.in_(user_group))
        owners_constraint = vs.models[model].owners.any(id=user.id)
        if hasattr(vs.models[model], "admin_only"):
            query = query.filter(vs.models[model].admin_only == false())
        return query.filter(or_(owners_constraint, rbac_constraint))

    def update_rbac(self):
        model = getattr(self, "class_type", None)
        if model not in vs.rbac["rbac_models"] or not current_user:
            return
        self.access_properties = defaultdict(list)
        self.owners = [current_user]
        for group in current_user.groups:
            for access_type in getattr(group, f"{model}_access"):
                if group not in getattr(self, access_type):
                    getattr(self, access_type).append(group)

    def delete(self):
        pass

    def get_properties(
        self, export=False, exclude=None, include=None, private_properties=False
    ):
        result = {}
        no_migrate = db.dont_migrate.get(getattr(self, "export_type", self.type), {})
        properties = list(vs.model_properties[self.type])
        for property in properties:
            if not private_properties and property in vs.private_properties_set:
                continue
            if property in db.dont_serialize.get(self.type, []):
                continue
            if export and property in getattr(self, "model_properties", {}):
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

    def table_properties(self, **kwargs):
        displayed = [column["data"] for column in kwargs["columns"]]
        table_type = getattr(self, "class_type", self.type)
        base = ["type"] if kwargs.get("rest_api_request") else ["id", "type"]
        additional = vs.properties["tables_additional"].get(table_type, [])
        return self.get_properties(include=base + displayed + additional)

    def duplicate(self, **kwargs):
        properties = {
            property: value
            for property, value in self.get_properties().items()
            if property not in ("id", "name")
        }
        instance = db.factory(self.type, rbac=None, **{**properties, **kwargs})
        return instance

    def to_dict(
        self,
        export=False,
        relation_names_only=False,
        exclude=None,
        include=None,
        private_properties=False,
    ):
        properties = self.get_properties(
            export, exclude=exclude, private_properties=private_properties
        )
        no_migrate = db.dont_migrate.get(getattr(self, "export_type", self.type), {})
        for property, relation in vs.relationships[self.type].items():
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

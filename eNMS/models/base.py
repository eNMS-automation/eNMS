from collections import defaultdict, OrderedDict
from flask_login import current_user
from re import search, sub
from sqlalchemy.ext.mutable import MutableDict, MutableList
from traceback import format_exc

from eNMS.database import db
from eNMS.environment import env
from eNMS.variables import vs


class AbstractBase(db.base):
    __abstract__ = True
    model_properties = {}

    def __init__(self, **kwargs):
        self.update(**kwargs)
        self.update_rbac()
        if not kwargs.get("migration_import"):
            self.creation_time = vs.get_time()

    def __lt__(self, other):
        return True

    def __repr__(self):
        return str(getattr(self, "name", self.id))

    def __getattribute__(self, property):
        if property in vs.private_properties_set:
            if env.use_vault:
                target = self.service if self.type == "run" else self
                path = f"secret/data/{target.type}/{target.name}/{property}"
                try:
                    data = env.vault_client.read(path)
                    value = data["data"]["data"][property] if data else ""
                except Exception:
                    value = ""
                    env.log("error", f"Cannot read Vault path {path}:\n{format_exc()}")
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

    @property
    def base_properties(self):
        return {prop: getattr(self, prop) for prop in ("id", "name", "type")}

    def delete(self):
        pass

    def duplicate(self, **kwargs):
        properties = {
            property: value
            for property, value in self.get_properties().items()
            if property not in ("id", "name")
        }
        instance = db.factory(self.type, rbac=None, **{**properties, **kwargs})
        return instance

    def exclude_soft_deleted(self, property):
        for instance in getattr(self, property):
            if not getattr(instance, "soft_deleted", False):
                yield instance

    def filter_rbac_kwargs(self, kwargs):
        if getattr(self, "class_type", None) not in vs.rbac["rbac_models"]:
            return
        rbac_properties = ["owners", "restrict_to_owners"]
        model_rbac_properties = list(vs.rbac["rbac_models"][self.class_type])
        is_admin = getattr(current_user, "is_admin", True)
        if not is_admin:
            kwargs.pop("admin_only", None)
            if current_user not in self.owners:
                for property in rbac_properties + model_rbac_properties:
                    kwargs.pop(property, None)

    @classmethod
    def filtering_constraints(cls, **_):
        return []

    def get_changelog_kwargs(self):
        return {
            "target_name": self.name,
            "target_type": self.type,
            "target_id": self.id,
            f"{self.class_type}_id": self.id,
        }

    def get_properties(
        self,
        export=False,
        exclude=None,
        include=None,
        private_properties=False,
        logging=False,
    ):
        result = {}
        no_migrate = db.dont_migrate.get(getattr(self, "export_type", self.type), {})
        properties = set(vs.model_properties[self.type])
        if include:
            properties &= set(include)
        for property in properties:
            if not private_properties and property in vs.private_properties_set:
                continue
            if logging:
                attribute = getattr(vs.models[self.type], property, None)
                if not getattr(attribute, "info", {}).get("log_change", True):
                    continue
            if property in db.dont_serialize.get(self.class_type, []):
                continue
            if export and property in getattr(self, "model_properties", {}):
                continue
            if exclude and property in exclude:
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

    def table_search(self, properties, **kwargs):
        columns = [column["data"] for column in kwargs["columns"]]
        rest_api_request = kwargs.get("rest_api_request")
        search_properties = {}
        context = int(kwargs["form"].get("context-lines", 0))
        for property in properties:
            if rest_api_request:
                if property in columns:
                    search_properties[property] = getattr(self, property)
                if f"{property}_matches" not in columns:
                    continue
            data = kwargs["form"].get(property)
            regex_match = kwargs["form"].get(f"{property}_filter") == "regex"
            if not data:
                search_properties[property] = ""
            else:
                result = []
                content, visited = getattr(self, property).splitlines(), set()
                for index, line in enumerate(content):
                    match_lines, merge = [], index - context - 1 in visited
                    if (
                        not search(data, line)
                        if regex_match
                        else data.lower() not in line.lower()
                    ):
                        continue
                    for i in range(-context, context + 1):
                        if index + i < 0 or index + i > len(content) - 1:
                            continue
                        if index + i in visited:
                            merge = True
                            continue
                        visited.add(index + i)
                        line = content[index + i].strip()
                        if rest_api_request:
                            match_lines.append(f"L{index + i + 1}: {line}")
                            continue
                        line = sub(f"(?i){data}", r"<mark>\g<0></mark>", line)
                        match_lines.append(f"<b>L{index + i + 1}:</b> {line}")
                    if rest_api_request:
                        result.extend(match_lines)
                    else:
                        if merge:
                            result[-1] += f"<br>{'<br>'.join(match_lines)}"
                        else:
                            result.append("<br>".join(match_lines))
                if rest_api_request:
                    search_properties[f"{property}_matches"] = result
                else:
                    search_properties[property] = "".join(
                        f"<pre style='text-align: left'>{match}</pre>"
                        for match in result
                    )
        return search_properties

    def to_dict(
        self,
        export=False,
        exclude=None,
        exclude_relations=None,
        include=None,
        include_relations=None,
        private_properties=False,
        relation_names_only=False,
        relation_properties=None,
    ):
        properties = self.get_properties(
            export,
            exclude=exclude,
            include=include,
            private_properties=private_properties,
        )
        no_migrate = db.dont_migrate.get(getattr(self, "export_type", self.type), {})
        for property, relation in vs.relationships[self.type].items():
            if include_relations and property not in include_relations:
                continue
            if exclude_relations and property in exclude_relations:
                continue
            if export and property in no_migrate:
                continue
            value = getattr(self, property)
            if relation["list"]:
                properties[property] = [
                    (
                        obj.name
                        if export or relation_names_only
                        else obj.get_properties(include=relation_properties)
                    )
                    for obj in value
                    if not getattr(obj, "soft_deleted", False)
                ]
                if export:
                    properties[property].sort()
            else:
                if not value or getattr(value, "soft_deleted", False):
                    continue
                properties[property] = (
                    value.name
                    if export or relation_names_only
                    else value.get_properties(include=relation_properties)
                )
        return dict(OrderedDict(sorted(properties.items()))) if export else properties

    @property
    def ui_name(self):
        return self.name

    def update(self, rbac="edit", **kwargs):
        self.filter_rbac_kwargs(kwargs)
        relation = vs.relationships[self.__tablename__]
        for property, value in kwargs.items():
            if not hasattr(self, property):
                continue
            property_type = vs.model_properties[self.__tablename__].get(property, None)
            if property in relation:
                if (
                    relation[property]["list"]
                    and value
                    and not hasattr(value[0], "__mapper__")
                ):
                    value = db.fetch_all(
                        relation[property]["model"], id_in=value, rbac=None
                    )
                elif value and not hasattr(value, "__mapper__"):
                    value = db.fetch(relation[property]["model"], id=value, rbac=None)
            if property_type == "bool":
                value = value not in (False, "false")
            elif property_type == "dict":
                table_properties = vs.properties["custom"].get(self.__tablename__, {})
                if table_properties.get(property, {}).get("merge_update"):
                    current_value = getattr(self, property)
                    if current_value:
                        value = {**current_value, **value}
            setattr(self, property, value)
        if not kwargs.get("migration_import"):
            self.update_last_modified_properties()
        if getattr(self, "class_type", None) not in vs.rbac["rbac_models"]:
            return
        for group in db.fetch_all("group", force_read_access=True, rbac=None):
            if group not in self.rbac_read:
                self.rbac_read.append(group)

    def update_last_modified_properties(self):
        self.last_modified = vs.get_time()
        self.last_modified_by = getattr(current_user, "name", "admin")

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

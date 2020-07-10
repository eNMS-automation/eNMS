from ast import literal_eval
from contextlib import contextmanager
from flask_login import current_user
from json import loads
from logging import error
from os import environ
from sqlalchemy import (
    Boolean,
    Column,
    create_engine,
    event,
    ForeignKey,
    Float,
    inspect,
    Integer,
    PickleType,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.mysql.base import MSMediumBlob
from sqlalchemy.ext.associationproxy import ASSOCIATION_PROXY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.types import JSON
from sqlalchemy.orm.collections import InstrumentedList
from time import sleep

from eNMS.models import model_properties, models, property_types, relationships
from eNMS.setup import database as database_settings, properties, settings


class Database:
    def __init__(self):
        for setting in database_settings.items():
            setattr(self, *setting)
        self.database_url = environ.get("DATABASE_URL", "sqlite:///database.db")
        self.dialect = self.database_url.split(":")[0]
        self.rbac_error = type("RbacError", (Exception,), {})
        self.configure_columns()
        self.engine = self.configure_engine()
        self.session = scoped_session(sessionmaker(autoflush=False, bind=self.engine))
        self.base = declarative_base()
        self.configure_associations()
        self.configure_events()
        self.field_conversion = {
            "bool": bool,
            "dict": self.dict_conversion,
            "float": float,
            "int": int,
            "integer": int,
            "json": loads,
            "list": str,
            "str": str,
            "date": str,
        }
        for retry_type, values in settings["database"]["retry"].items():
            for parameter, number in values.items():
                setattr(self, f"retry_{retry_type}_{parameter}", number)

    @staticmethod
    def dict_conversion(input):
        try:
            return literal_eval(input)
        except Exception:
            return loads(input)

    def configure_engine(self):
        engine_parameters = {
            "convert_unicode": True,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        }
        if self.dialect == "mysql":
            engine_parameters.update(
                {
                    "max_overflow": settings["database"]["max_overflow"],
                    "pool_size": settings["database"]["pool_size"],
                    "isolation_level": "READ COMMITTED",
                }
            )
        elif self.dialect == "sqlite":
            engine_parameters["connect_args"] = {"check_same_thread": False}
        return create_engine(self.database_url, **engine_parameters)

    def configure_columns(self):
        class CustomPickleType(PickleType):
            if self.dialect == "mysql":
                impl = MSMediumBlob

        self.Dict = MutableDict.as_mutable(CustomPickleType)
        self.List = MutableList.as_mutable(CustomPickleType)
        if self.dialect == "postgresql":
            self.LargeString = Text
        else:
            self.LargeString = Text(settings["database"]["large_string_length"])
        self.SmallString = String(settings["database"]["small_string_length"])

        default_ctypes = {
            self.Dict: {},
            self.List: [],
            self.LargeString: "",
            self.SmallString: "",
            Text: "",
        }

        class CustomColumn(Column):
            def __init__(self, ctype, *args, **kwargs):
                if "default" not in kwargs and ctype in default_ctypes:
                    kwargs["default"] = default_ctypes[ctype]
                super().__init__(ctype, *args, **kwargs)

        self.Column = CustomColumn

    def configure_events(self):
        @event.listens_for(self.base, "mapper_configured", propagate=True)
        def model_inspection(mapper, model):
            name = model.__tablename__
            for col in inspect(model).columns:
                if not col.info.get("model_properties", True):
                    continue
                model_properties[name].append(col.key)
                if col.type == PickleType and isinstance(col.default.arg, list):
                    property_types[col.key] = "list"
                else:
                    column_type = {
                        Boolean: "bool",
                        Integer: "int",
                        Float: "float",
                        JSON: "dict",
                        PickleType: "dict",
                    }.get(type(col.type), "str")
                    if col.key not in property_types:
                        property_types[col.key] = column_type
            for descriptor in inspect(model).all_orm_descriptors:
                if descriptor.extension_type is ASSOCIATION_PROXY:
                    property = (
                        descriptor.info.get("name")
                        or f"{descriptor.target_collection}_{descriptor.value_attr}"
                    )
                    model_properties[name].append(property)
            if hasattr(model, "parent_type"):
                model_properties[name].extend(model_properties[model.parent_type])
            if "service" in name and name != "service":
                model_properties[name].extend(model_properties["service"])
            models.update({name: model, name.lower(): model})
            model_properties[name].extend(model.model_properties)
            model_properties[name] = list(set(model_properties[name]))
            for relation in mapper.relationships:
                if getattr(relation.mapper.class_, "private", False):
                    continue
                property = str(relation).split(".")[1]
                relationships[name][property] = {
                    "model": relation.mapper.class_.__tablename__,
                    "list": relation.uselist,
                }

    def configure_application_events(self, app):
        @event.listens_for(self.base, "after_insert", propagate=True)
        def log_instance_creation(mapper, connection, target):
            if hasattr(target, "name"):
                app.log("info", f"CREATION: {target.type} '{target.name}'")

        @event.listens_for(self.base, "before_delete", propagate=True)
        def log_instance_deletion(mapper, connection, target):
            name = getattr(target, "name", str(target))
            app.log("info", f"DELETION: {target.type} '{name}'")

        @event.listens_for(self.base, "before_update", propagate=True)
        def log_instance_update(mapper, connection, target):
            state, changelog = inspect(target), []
            for attr in state.attrs:
                hist = state.get_history(attr.key, True)
                if (
                    getattr(target, "private", False)
                    or not getattr(target, "log_changes", True)
                    or not getattr(state.class_, attr.key).info.get("log_change", True)
                    or attr.key in self.private_properties
                    or not hist.has_changes()
                ):
                    continue
                change = f"{attr.key}: "
                property_type = type(getattr(target, attr.key))
                if property_type in (InstrumentedList, MutableList):
                    if property_type == MutableList:
                        added = [x for x in hist.added[0] if x not in hist.deleted[0]]
                        deleted = [x for x in hist.deleted[0] if x not in hist.added[0]]
                    else:
                        added, deleted = hist.added, hist.deleted
                    if deleted:
                        change += f"DELETED: {deleted}"
                    if added:
                        change += f"{' / ' if deleted else ''}ADDED: {added}"
                else:
                    change += (
                        f"'{hist.deleted[0] if hist.deleted else None}' => "
                        f"'{hist.added[0] if hist.added else None}'"
                    )
                changelog.append(change)
            if changelog:
                name, changes = (
                    getattr(target, "name", target.id),
                    " | ".join(changelog),
                )
                app.log("info", f"UPDATE: {target.type} '{name}': ({changes})")

        if app.use_vault:

            @event.listens_for(models["service"].name, "set", propagate=True)
            def vault_update(target, new_value, old_value, *_):
                path = f"secret/data/{target.type}/{old_value}/password"
                data = app.vault_client.read(path)
                if not data:
                    return
                app.vault_client.write(
                    f"secret/data/{target.type}/{new_value}/password",
                    data={"password": data["data"]["data"]["password"]},
                )

    def configure_associations(self):
        for model1, model2 in self.many_to_many_relationships:
            kw = {"ondelete": "cascade"} if model1 == "run" else {}
            setattr(
                self,
                f"{model1}_{model2}_table",
                Table(
                    f"{model1}_{model2}_association",
                    self.base.metadata,
                    Column(f"{model1}_id", Integer, ForeignKey(f"{model1}.id", **kw)),
                    Column(f"{model2}_id", Integer, ForeignKey(f"{model2}.id")),
                ),
            )
        self.originals_association = Table(
            "originals_association",
            self.base.metadata,
            Column("original_id", Integer, ForeignKey("service.id"), primary_key=True),
            Column("child_id", Integer, ForeignKey("service.id"), primary_key=True),
        )

    def fetch(self, model, allow_none=False, all_matches=False, rbac="read", **kwargs):
        query = self.query(model, rbac).filter_by(**kwargs)
        for index in range(self.retry_fetch_number):
            try:
                result = query.all() if all_matches else query.first()
                break
            except Exception as exc:
                error(f"Fetch n°{index} failed ({exc})")
                self.session.rollback()
                if index == self.retry_fetch_number - 1:
                    raise exc
                sleep(self.retry_fetch_time * (index + 1))
        if result or allow_none:
            return result
        else:
            raise db.rbac_error(
                f"There is no {model} in the database "
                f"with the following characteristics: {kwargs}"
            )

    def query(self, model, rbac="read", username=None):
        query = self.session.query(models[model])
        if rbac and model != "user":
            if current_user:
                user = current_user
            else:
                user = self.fetch("user", name=username or "admin")
            if user.is_authenticated and not user.is_admin:
                query = models[model].rbac_filter(query, rbac, user)
        return query

    def fetch_all(self, model, **kwargs):
        return self.fetch(model, allow_none=True, all_matches=True, **kwargs)

    def objectify(self, model, object_list):
        return [self.fetch(model, id=object_id) for object_id in object_list]

    def delete(self, model, allow_none=False, **kwargs):
        instance = self.session.query(models[model]).filter_by(**kwargs).first()
        if allow_none and not instance:
            return None
        return self.delete_instance(instance)

    def delete_instance(self, instance):
        try:
            instance.delete()
        except Exception as exc:
            return {"alert": f"Unable to delete {instance.name} ({exc})."}
        serialized_instance = instance.serialized
        self.session.delete(instance)
        return serialized_instance

    def delete_all(self, *models):
        for model in models:
            for instance in self.fetch_all(model):
                self.delete_instance(instance)
            self.session.commit()

    def export(self, model):
        return [instance.to_dict(export=True) for instance in self.fetch_all(model)]

    def factory(self, _class, commit=False, **kwargs):
        def transaction(_class, **kwargs):
            characters = set(kwargs.get("name", "") + kwargs.get("scoped_name", ""))
            if set("/\\'" + '"') & characters:
                raise Exception("Names cannot contain a slash or a quote.")
            instance, instance_id = None, kwargs.pop("id", 0)
            if instance_id:
                instance = self.fetch(_class, id=instance_id, rbac="edit")
            elif "name" in kwargs:
                instance = self.fetch(
                    _class, allow_none=True, name=kwargs["name"], rbac="edit"
                )
            if instance and not kwargs.get("must_be_new"):
                instance.update(**kwargs)
            else:
                instance = models[_class](**kwargs)
                self.session.add(instance)
            return instance

        if not commit:
            instance = transaction(_class, **kwargs)
        else:
            for index in range(self.retry_commit_number):
                try:
                    instance = transaction(_class, **kwargs)
                    self.session.commit()
                    break
                except Exception as exc:
                    error(f"Commit n°{index} failed ({exc})")
                    self.session.rollback()
                    if index == self.retry_commit_number - 1:
                        raise exc
                    sleep(self.retry_commit_time * (index + 1))
        return instance

    @contextmanager
    def session_scope(self):
        try:
            yield self.session
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        finally:
            self.session.close()

    def set_custom_properties(self, table):
        model = table.__tablename__
        for property, values in properties["custom"].get(model, {}).items():
            if values.get("private", False):
                kwargs = {}
            else:
                kwargs = {
                    "default": values["default"],
                    "info": {"log_change": values.get("log_change", True)},
                }
            column = self.Column(
                {
                    "boolean": Boolean,
                    "dict": self.Dict,
                    "float": Float,
                    "integer": Integer,
                    "json": JSON,
                    "string": self.LargeString,
                    "select": self.SmallString,
                    "multiselect": self.List,
                }[values.get("type", "string")],
                **kwargs,
            )
            if not values.get("serialize", True):
                self.dont_serialize[model].append(property)
            if not values.get("migrate", True):
                self.dont_migrate[model].append(property)
            setattr(table, property, column)
        return table


db = Database()

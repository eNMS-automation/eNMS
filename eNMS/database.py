from ast import literal_eval
from atexit import register
from contextlib import contextmanager
from flask_login import current_user
from importlib.util import module_from_spec, spec_from_file_location
from json import loads
from logging import error, info, warning
from operator import attrgetter
from os import getenv, getpid
from os.path import exists
from pathlib import Path
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
from sqlalchemy.exc import InvalidRequestError, OperationalError
from sqlalchemy.ext.associationproxy import AssociationProxyExtensionType
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import (
    configure_mappers,
    relationship,
    scoped_session,
    sessionmaker,
)
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.types import JSON
from time import sleep
from traceback import format_exc
from uuid import getnode

from eNMS.variables import vs


class Database:
    def __init__(self):
        for setting in vs.database.items():
            setattr(self, *setting)
        self.database_url = getenv("DATABASE_URL", "sqlite:///database.db")
        self.dialect = self.database_url.split(":")[0]
        self.rbac_error = type("RbacError", (Exception,), {})
        self.configure_columns()
        self.engine = create_engine(
            self.database_url,
            **self.engine["common"],
            **self.engine.get(self.dialect, {}),
        )
        self.session = scoped_session(sessionmaker(autoflush=False, bind=self.engine))
        self.base = declarative_base(metaclass=self.create_metabase())
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
        for retry_type, values in self.transactions["retry"].items():
            for parameter, number in values.items():
                setattr(self, f"retry_{retry_type}_{parameter}", number)
        register(self.cleanup)

    def _initialize(self, env):
        self.register_custom_models()
        try:
            self.base.metadata.create_all(bind=self.engine)
        except OperationalError:
            info(f"Bypassing metadata creation for process {getpid()}")
        configure_mappers()
        self.configure_model_events(env)
        if env.detect_cli():
            return
        first_init = not self.fetch("user", allow_none=True, name="admin")
        if first_init:
            admin_user = vs.models["user"](name="admin", is_admin=True)
            self.session.add(admin_user)
            self.session.commit()
            if not admin_user.password:
                admin_user.update(password="admin")
            self.factory(
                "server",
                **{
                    "name": vs.server,
                    "description": vs.server,
                    "mac_address": str(getnode()),
                    "ip_address": vs.server_ip,
                    "scheduler_address": vs.scheduler_address,
                    "scheduler_active": vs.scheduler_active,
                    "location": vs.server_location,
                    "status": "Up",
                },
            )
            parameters = self.factory(
                "parameters",
                **{
                    f"banner_{property}": vs.settings["notification_banner"][property]
                    for property in ("active", "deactivate_on_restart", "properties")
                },
            )
        self.session.commit()
        server = db.factory(
            "server",
            name=vs.server,
            version=vs.server_version,
            commit_sha=vs.server_commit_sha,
            last_restart=vs.get_time(),
        )
        for worker in server.workers:
            if not exists(f"/proc/{worker.name}"):
                db.delete_instance(worker, call_delete=False)
        vs.server_id = server.id
        for run in self.fetch(
            "run", all_matches=True, allow_none=True, status="Running"
        ):
            run.status = "Aborted (RELOAD)"
            run.service.status = "Idle"
        parameters = self.fetch("parameters")
        if parameters.banner_deactivate_on_restart:
            parameters.banner_active = False
        self.session.commit()
        return first_init

    def create_metabase(self):
        class SubDeclarativeMeta(DeclarativeMeta):
            def __init__(cls, *args):  # noqa: N805
                DeclarativeMeta.__init__(cls, *args)
                if hasattr(cls, "database_init") and "database_init" in cls.__dict__:
                    cls.database_init()
                self.set_custom_properties(cls)
                self.set_rbac_properties(cls)

        return SubDeclarativeMeta

    @staticmethod
    def dict_conversion(input):
        try:
            return literal_eval(input)
        except Exception:
            return loads(input)

    def configure_columns(self):
        class CustomPickleType(PickleType):
            cache_ok = True
            if self.dialect.startswith(("mariadb", "mysql")):
                impl = MSMediumBlob

        self.Dict = MutableDict.as_mutable(CustomPickleType)
        self.List = MutableList.as_mutable(CustomPickleType)
        if self.dialect == "postgresql":
            self.LargeString = Text
        else:
            self.LargeString = Text(self.columns["length"]["large_string"])
        self.SmallString = String(self.columns["length"]["small_string"])
        self.TinyString = String(self.columns["length"]["tiny_string"])

        default_ctypes = {
            self.Dict: {},
            self.List: [],
            self.LargeString: "",
            self.SmallString: "",
            self.TinyString: "",
            Text: "",
        }

        def init_column(column_type, *args, **kwargs):
            if "default" not in kwargs and column_type in default_ctypes:
                kwargs["default"] = default_ctypes[column_type]
            return Column(column_type, *args, **kwargs)

        self.Column = init_column

    def configure_events(self):
        @event.listens_for(self.base, "mapper_configured", propagate=True)
        def model_inspection(mapper, model):
            name = model.__tablename__
            for col in inspect(model).columns:
                if not col.info.get("model_properties", True):
                    continue
                if col.type == PickleType:
                    is_list = isinstance(col.default.arg, list)
                    property_type = "list" if is_list else "dict"
                else:
                    property_type = {
                        Boolean: "bool",
                        Integer: "int",
                        Float: "float",
                        JSON: "dict",
                    }.get(type(col.type), "str")
                vs.model_properties[name][col.key] = property_type
            for descriptor in inspect(model).all_orm_descriptors:
                association_proxy = AssociationProxyExtensionType.ASSOCIATION_PROXY
                if descriptor.extension_type is association_proxy:
                    property = (
                        descriptor.info.get("name")
                        or f"{descriptor.target_collection}_{descriptor.value_attr}"
                    )
                    vs.model_properties[name][property] = "str"
            if hasattr(model, "parent_type"):
                vs.model_properties[name].update(vs.model_properties[model.parent_type])
            if "service" in name and name != "service":
                vs.model_properties[name].update(vs.model_properties["service"])
            vs.models.update({name: model, name.lower(): model})
            vs.model_properties[name].update(model.model_properties)
            for relation in mapper.relationships:
                if getattr(relation.mapper.class_, "private", False):
                    continue
                property = str(relation).split(".")[1]
                vs.relationships[name][property] = {
                    "model": relation.mapper.class_.__tablename__,
                    "list": relation.uselist,
                }

    def configure_model_events(self, env):
        env.log_events = True

        @event.listens_for(self.base, "after_insert", propagate=True)
        def log_instance_creation(mapper, connection, target):
            if not getattr(target, "log_change", True) or not env.log_events:
                return
            if hasattr(target, "name") and target.type != "run":
                env.log("info", f"CREATION: {target.type} '{target.name}'")

        @event.listens_for(self.base, "before_delete", propagate=True)
        def log_instance_deletion(mapper, connection, target):
            if not getattr(target, "log_change", True) or not env.log_events:
                return
            name = getattr(target, "name", str(target))
            env.log("info", f"DELETION: {target.type} '{name}'")

        @event.listens_for(self.base, "before_update", propagate=True)
        def log_instance_update(mapper, connection, target):
            if not env.log_events:
                return
            state, changelog = inspect(target), []
            for attr in state.attrs:
                hist = state.get_history(attr.key, True)
                if (
                    getattr(target, "private", False)
                    or not getattr(target, "log_change", True)
                    or not getattr(state.class_, attr.key).info.get("log_change", True)
                    or attr.key in vs.private_properties_set
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
                env.log("info", f"UPDATE: {target.type} '{name}': ({changes})")

        for model in vs.models.values():
            if "configure_events" in vars(model):
                model.configure_events()

        if env.use_vault:
            for model in vs.private_properties:

                @event.listens_for(vs.models[model].name, "set", propagate=True)
                def vault_update(target, new_name, old_name, *_):
                    if new_name == old_name:
                        return
                    for property in vs.private_properties[target.class_type]:
                        path = f"secret/data/{target.type}"
                        data = env.vault_client.read(f"{path}/{old_name}/{property}")
                        if not data:
                            return
                        env.vault_client.write(
                            f"{path}/{new_name}/{property}",
                            data={property: data["data"]["data"][property]},
                        )
                        env.vault_client.delete(f"{path}/{old_name}")

    def configure_associations(self):
        for name, association in self.relationships["associations"].items():
            model1, model2 = association["model1"], association["model2"]
            setattr(
                self,
                f"{name}_table",
                Table(
                    f"{name}_association",
                    self.base.metadata,
                    Column(
                        model1["column"],
                        Integer,
                        ForeignKey(
                            f"{model1['foreign_key']}.id", **model1.get("kwargs", {})
                        ),
                        primary_key=True,
                    ),
                    Column(
                        model2["column"],
                        Integer,
                        ForeignKey(
                            f"{model2['foreign_key']}.id", **model2.get("kwargs", {})
                        ),
                        primary_key=True,
                    ),
                ),
            )
        for model, properties in vs.rbac["rbac_models"].items():
            setattr(
                self,
                f"{model}_owner_table",
                Table(
                    f"{model}_owner_association",
                    self.base.metadata,
                    Column(
                        f"{model}_id",
                        Integer,
                        ForeignKey(f"{model}.id"),
                        primary_key=True,
                    ),
                    Column("user_id", Integer, ForeignKey("user.id"), primary_key=True),
                ),
            )
            for property in properties:
                setattr(
                    self,
                    f"{model}_{property}_table",
                    Table(
                        f"{model}_{property}_association",
                        self.base.metadata,
                        Column(
                            f"{model}_id",
                            Integer,
                            ForeignKey(f"{model}.id"),
                            primary_key=True,
                        ),
                        Column(
                            "group_id",
                            Integer,
                            ForeignKey("group.id"),
                            primary_key=True,
                        ),
                    ),
                )
        for property in vs.rbac["rbac_models"]["device"]:
            setattr(
                self,
                f"pool_group_{property}_table",
                Table(
                    f"pool_group_{property}_association",
                    self.base.metadata,
                    Column(
                        "pool_id",
                        Integer,
                        ForeignKey("pool.id"),
                        primary_key=True,
                    ),
                    Column(
                        "group_id",
                        Integer,
                        ForeignKey("group.id"),
                        primary_key=True,
                    ),
                ),
            )

    def query(self, model, rbac="read", username=None, properties=None):
        if properties:
            entity = [getattr(vs.models[model], property) for property in properties]
        else:
            entity = [vs.models[model]]
        query = self.session.query(*entity)
        if rbac:
            user = (
                current_user
                or self.session.query(vs.models["user"])
                .filter_by(name=username or "admin")
                .first()
            )
            if not user:
                return
            if user.is_authenticated and not user.is_admin:
                if model in vs.rbac["admin_models"].get(rbac, []):
                    raise self.rbac_error
                query = vs.models[model].rbac_filter(query, rbac, user)
        return query

    def fetch(
        self,
        instance_type,
        allow_none=False,
        all_matches=False,
        rbac="read",
        username=None,
        **kwargs,
    ):
        query = self.query(instance_type, rbac, username=username)
        if not query:
            return
        query = query.filter(
            *(
                getattr(vs.models[instance_type], key) == value
                for key, value in kwargs.items()
            )
        )
        for index in range(self.retry_fetch_number):
            try:
                result = query.all() if all_matches else query.first()
                break
            except Exception as exc:
                self.session.rollback()
                if index == self.retry_fetch_number - 1:
                    error(f"Fetch n°{index} failed ({format_exc()})")
                    raise exc
                else:
                    warning(f"Fetch n°{index} failed ({str(exc)})")
                sleep(self.retry_fetch_time * (index + 1))
        if result or allow_none:
            return result
        else:
            raise self.rbac_error(
                f"There is no {instance_type} in the database "
                f"with the following characteristics: {kwargs}"
            )

    def delete(self, model, **kwargs):
        instance = self.fetch(model, **{"rbac": "edit", **kwargs})
        return self.delete_instance(instance)

    def fetch_all(self, model, **kwargs):
        return self.fetch(model, allow_none=True, all_matches=True, **kwargs)

    def objectify(self, model, object_list, **kwargs):
        return [self.fetch(model, id=object_id, **kwargs) for object_id in object_list]

    def delete_instance(self, instance, call_delete=True):
        abort_delete = False
        if call_delete:
            abort_delete = instance.delete()
            if abort_delete:
                return {"delete_aborted": True, "log_level": "error", **abort_delete}
        serialized_instance = instance.serialized
        if not abort_delete:
            self.session.delete(instance)
        return serialized_instance

    def delete_all(self, *models):
        for model in models:
            for instance in self.fetch_all(model):
                self.delete_instance(instance, call_delete=model != "file")
            self.session.commit()

    def export(self, model, private_properties=False):
        return [
            instance.to_dict(export=True, private_properties=private_properties)
            for instance in self.fetch_all(model)
        ]

    def factory(self, _class, commit=False, no_fetch=False, rbac="edit", **kwargs):
        def transaction(_class, **kwargs):
            property = "path" if _class in ("file", "folder") else "name"
            characters = set(kwargs.get("name", "") + kwargs.get("scoped_name", ""))
            if set("/\\'" + '"') & characters:
                raise Exception("Names cannot contain a slash or a quote.")
            instance, instance_id = None, kwargs.pop("id", 0)
            if instance_id:
                instance = self.fetch(_class, id=instance_id, rbac=rbac)
            elif property in kwargs and not no_fetch:
                instance = self.fetch(
                    _class, allow_none=True, rbac=rbac, **{property: kwargs[property]}
                )
            if instance and not kwargs.get("must_be_new"):
                instance.update(rbac=rbac, **kwargs)
            else:
                instance = vs.models[_class](rbac=rbac, **kwargs)
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
                    self.session.rollback()
                    if index == self.retry_commit_number - 1:
                        error(f"Commit n°{index} failed ({format_exc()})")
                        raise exc
                    else:
                        warning(f"Commit n°{index} failed ({str(exc)})")
                    sleep(self.retry_commit_time * (index + 1))
        return instance

    def get_credential(
        self, username, name=None, device=None, credential_type="any", optional=False
    ):
        query = (
            self.session.query(vs.models["credential"])
            .join(vs.models["group"], vs.models["credential"].groups)
            .join(vs.models["user"], vs.models["group"].users)
        )
        if device:
            query = query.join(
                vs.models["pool"], vs.models["credential"].device_pools
            ).join(vs.models["device"], vs.models["pool"].devices)
        query = query.filter(vs.models["user"].name == username)
        if name:
            query = query.filter(vs.models["credential"].name == name)
        if device:
            query = query.filter(vs.models["device"].name == device.name)
        if credential_type != "any":
            query = query.filter(vs.models["credential"].role == credential_type)
        credentials = max(query.all(), key=attrgetter("priority"), default=None)
        if not credentials and not optional:
            raise Exception(f"No matching credentials found for DEVICE '{device.name}'")
        return credentials

    def register_custom_models(self):
        for model in ("device", "link", "service"):
            paths = [vs.path / "eNMS" / "models" / f"{model}s"]
            load_examples = vs.settings["app"].get("startup_migration") == "examples"
            if vs.settings["paths"][f"custom_{model}s"]:
                paths.append(Path(vs.settings["paths"][f"custom_{model}s"]))
            for path in paths:
                for file in path.glob("**/*.py"):
                    if "init" in str(file):
                        continue
                    if not load_examples and "examples" in str(file):
                        continue
                    info(f"Loading {model}: {file}")
                    spec = spec_from_file_location(file.stem, str(file))
                    try:
                        spec.loader.exec_module(module_from_spec(spec))
                    except InvalidRequestError:
                        error(f"Error loading {model} '{file}'\n{format_exc()}")

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
        model = getattr(table, "__tablename__", None)
        if not model:
            return
        for property, values in vs.properties["custom"].get(model, {}).items():
            if values.get("private", False):
                kwargs = {}
            else:
                if "default_function" in values:
                    values["default"] = getattr(vs.custom, values["default_function"])
                kwargs = {
                    "default": values["default"],
                    "info": {"log_change": values.get("log_change", True)},
                }
            column = self.Column(
                {
                    "bool": Boolean,
                    "dict": self.Dict,
                    "float": Float,
                    "integer": Integer,
                    "json": JSON,
                    "str": self.LargeString,
                    "select": self.SmallString,
                    "multiselect": self.List,
                }[values.get("type", "str")],
                **kwargs,
            )
            if not values.get("serialize", True):
                self.dont_serialize[model].append(property)
            if not values.get("migrate", True):
                self.dont_migrate[model].append(property)
            setattr(table, property, column)

    def set_rbac_properties(self, table):
        model = getattr(table, "__tablename__", None)
        if model == "user":
            for rbac_model in vs.rbac["rbac_models"]:
                setattr(
                    table,
                    f"user_{rbac_model}s",
                    relationship(
                        rbac_model.capitalize(),
                        secondary=getattr(self, f"{rbac_model}_owner_table"),
                        back_populates="owners",
                    ),
                )
        properties = vs.rbac["rbac_models"].get(model, {})
        if not model or not properties:
            return
        setattr(
            table,
            "owners",
            relationship(
                "User",
                secondary=getattr(self, f"{model}_owner_table"),
                back_populates=f"user_{model}s",
            ),
        )
        for property in properties:
            setattr(
                table,
                property,
                relationship(
                    "Group",
                    secondary=getattr(self, f"{model}_{property}_table"),
                    back_populates=f"{property}_{model}s",
                ),
            )

    def cleanup(self):
        self.engine.dispose()


db = Database()

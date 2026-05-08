from ast import literal_eval
from atexit import register
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import datetime, timedelta
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
    Float,
    ForeignKey,
    inspect,
    Integer,
    PickleType,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.mysql.base import LONGTEXT, MEDIUMTEXT, MSMediumBlob
from sqlalchemy.exc import IntegrityError, InvalidRequestError, OperationalError
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
from traceback import extract_stack, format_exc
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
            error(f"Error during metadata creation (PID {getpid()}):\n{format_exc()}")
        configure_mappers()
        self.configure_model_events(env)
        if env.detect_cli() or env.file_watcher:
            return
        first_init = not self.fetch("user", allow_none=True, rbac=None, name="admin")
        if first_init:
            admin_user = vs.models["user"](name="admin", is_admin=True)
            self.session.add(admin_user)
            self.session.commit()
            if not admin_user.password:
                admin_user.update(password="admin")
            self.factory(
                "server",
                rbac=None,
                **{
                    "name": vs.server,
                    "description": vs.server,
                    "role": vs.server_role,
                    "mac_address": str(getnode()),
                    "ip_address": vs.server_ip,
                    "scheduler_address": vs.scheduler_address,
                    "scheduler_active": vs.scheduler_active,
                    "location": vs.server_location,
                    "allowed_automation": vs.settings["cluster"]["allowed_automation"],
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
            rbac=None,
            name=vs.server,
            version=vs.server_version,
            commit_sha=vs.server_commit_sha,
            last_restart=vs.get_time(),
            commit=True,
        )
        for worker in server.workers:
            if exists(f"/proc/{worker.process_id}"):
                continue
            try:
                db.delete_instance(worker, call_delete=False)
                db.session.commit()
            except Exception:
                db.session.rollback()
        vs.server_id = server.id
        parameters = self.fetch("parameters", rbac=None)
        if parameters.banner_deactivate_on_restart:
            parameters.banner_active = False
        self.session.commit()
        return first_init

    def cleanup(self):
        self.engine.dispose()

    def configure_associations(self):
        self.associations = {}
        for name, association in self.relationships["associations"].items():
            model1, model2 = association["model1"], association["model2"]
            table = Table(
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
            )
            setattr(self, f"{name}_table", table)
            self.associations[f"{name}_table"] = {"table": table, **association}
        for model, properties in vs.rbac["rbac_models"].items():
            table = Table(
                f"{model}_owner_association",
                self.base.metadata,
                Column(
                    f"{model}_id",
                    Integer,
                    ForeignKey(f"{model}.id"),
                    primary_key=True,
                ),
                Column("user_id", Integer, ForeignKey("user.id"), primary_key=True),
            )
            association = {
                "model1": {"foreign_key": model},
                "model2": {"foreign_key": "user"},
            }
            self.associations[f"{model}_owner_table"] = {"table": table, **association}
            setattr(self, f"{model}_owner_table", table)
            for property in properties:
                table = Table(
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
                )
                association = {
                    "model1": {"foreign_key": model},
                    "model2": {"foreign_key": "group"},
                }
                self.associations[f"{model}_{property}_table"] = {
                    "table": table,
                    **association,
                }
                setattr(self, f"{model}_{property}_table", table)
        for property in vs.rbac["rbac_models"]["device"]:
            table = Table(
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
            )
            association = {
                "model1": {"foreign_key": "pool"},
                "model2": {"foreign_key": "group"},
            }
            self.associations[f"pool_group_{property}_table"] = {
                "table": table,
                **association,
            }
            setattr(self, f"pool_group_{property}_table", table)

    def configure_columns(self):
        class CustomPickleType(PickleType):
            cache_ok = True
            if self.dialect.startswith(("mariadb", "mysql")):
                impl = MSMediumBlob

        self.Dict = MutableDict.as_mutable(CustomPickleType)
        self.List = MutableList.as_mutable(CustomPickleType)
        if self.dialect == "postgresql":
            self.LargeString = self.MediumString = Text
        else:
            self.LargeString = Text(
                self.columns["length"]["large_string"]
            ).with_variant(LONGTEXT, "mysql", "mariadb")
            self.MediumString = Text(
                self.columns["length"]["medium_string"]
            ).with_variant(MEDIUMTEXT, "mysql", "mariadb")
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
            if (
                "service" in name
                and name != "service"
                and issubclass(model, vs.models["service"])
            ):
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
            if (
                not getattr(target, "log_change", True)
                or not env.log_events
                or connection.info.get("ignore")
            ):
                return
            if hasattr(target, "name") and target.type != "run":
                properties = target.get_properties(logging=True)
                content = f"CREATION: {target.type} '{target.name}' ({properties})"
                env.log("info", content, instance=target, history={"creation": True})

        @event.listens_for(self.base, "before_delete", propagate=True)
        def log_instance_deletion(mapper, connection, target):
            if (
                not getattr(target, "log_change", True)
                or not env.log_events
                or connection.info.get("ignore")
            ):
                return
            name = getattr(target, "name", str(target))
            env.log("info", f"DELETION: {target.type} '{name}'")

        @event.listens_for(self.base, "before_update", propagate=True)
        def log_instance_update(mapper, connection, target):
            if not env.log_events or connection.info.get("ignore"):
                return
            state, changelog, history = inspect(target), [], defaultdict(dict)
            for attr in state.attrs:
                hist = state.get_history(attr.key, True)
                if (
                    getattr(target, "private", False)
                    or not getattr(target, "log_change", True)
                    or not getattr(state.class_, attr.key).info.get("log_change", True)
                    or not hist.has_changes()
                ):
                    continue
                change, added, deleted = f"{attr.key}: ", hist.added, hist.deleted
                property_type = type(getattr(target, attr.key))
                if attr.key in vs.private_properties_set:
                    change += "updated"
                elif property_type in (InstrumentedList, MutableList):
                    if property_type == MutableList:
                        # when reverting a changelog for a db.List property,
                        # hist.deleted is improperly set as a tuple
                        if isinstance(added, tuple) or isinstance(deleted, tuple):
                            continue
                        added, deleted = (
                            [x for x in added[0] if x not in deleted[0]],
                            [x for x in deleted[0] if x not in added[0]],
                        )
                    if not added and not deleted:
                        continue
                    history["lists"][attr.key] = {
                        "added": [getattr(x, "id", x) for x in added],
                        "deleted": [getattr(x, "id", x) for x in deleted],
                        "type": getattr(
                            (added[0] if added else deleted[0]), "class_type", "str"
                        ),
                    }
                    if deleted:
                        change += f" - Removed: {deleted}"
                    if added:
                        change += f" - Added: {added}"
                    history["properties"][attr.key] = {
                        "old": "\n".join(map(str, deleted)),
                        "new": "\n".join(map(str, added)),
                    }
                else:
                    if deleted:
                        if hasattr(deleted[0], "class_type"):
                            history["scalars"][attr.key] = deleted[0].base_properties
                        else:
                            change_dict = {"old": deleted[0], "new": added[0]}
                            history["properties"][attr.key] = change_dict
                    change += (
                        f"'{deleted[0] if deleted else None}' => "
                        f"'{added[0] if added else None}'"
                    )
                changelog.append(change)
            if changelog:
                name, changes = (
                    getattr(target, "name", target.id),
                    "\n- " + "\n- ".join(changelog),
                )
                log_content = f"UPDATE: {target.type} '{name}':\n{changes}"
                env.log(
                    "info",
                    log_content,
                    instance=target,
                    history=history,
                    source=connection.info.pop(
                        f"update_{target.type}_{target.name}", None
                    ),
                )

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

        if vs.settings["app"]["config_mode"].lower() == "debug":
            self.orm_statements = Counter()
            self.orm_statements_runtime = defaultdict(timedelta)
            self.orm_statements_tracebacks = defaultdict(lambda: defaultdict(int))

            self.monitor_orm_statements = False

            @event.listens_for(self.engine, "before_cursor_execute")
            def before_cursor_execute(*args):
                if not self.monitor_orm_statements:
                    return
                args[4]._start = datetime.now()

            @event.listens_for(self.engine, "after_cursor_execute")
            def after_cursor_execute(*args):
                statement, context = args[2], args[4]
                if not self.monitor_orm_statements or not hasattr(context, "_start"):
                    return
                runtime = datetime.now() - context._start
                self.orm_statements[statement] += 1
                self.orm_statements_runtime[statement] += runtime
                traceback = "\n".join(
                    f"{frame.filename}:{frame.lineno} in {frame.name}"
                    for frame in extract_stack()
                    if "enms" in frame.filename.lower()
                )
                self.orm_statements_tracebacks[statement][traceback] += 1

    def create_metabase(self):
        class SubDeclarativeMeta(DeclarativeMeta):
            def __init__(cls, *args):  # noqa: N805
                DeclarativeMeta.__init__(cls, *args)
                if hasattr(cls, "database_init") and "database_init" in cls.__dict__:
                    cls.database_init()
                self.set_custom_properties(cls)
                self.set_rbac_properties(cls)

        return SubDeclarativeMeta

    def delete(self, model, **kwargs):
        instance = self.fetch(model, **{"rbac": "edit", **kwargs})
        return self.delete_instance(instance)

    def delete_all(self, *models):
        for model in models:
            for instance in self.fetch_all(model):
                self.delete_instance(instance, call_delete=model != "file")
            self.session.commit()

    def delete_instance(self, instance, call_delete=True):
        abort_delete = False
        if call_delete:
            abort_delete = instance.delete()
            if abort_delete:
                return {"delete_aborted": True, "log_level": "error", **abort_delete}
        serialized_instance = instance.get_properties()
        if not abort_delete:
            self.session.delete(instance)
        return serialized_instance

    @staticmethod
    def dict_conversion(input):
        try:
            return literal_eval(input)
        except Exception:
            return loads(input)

    def export(self, model, private_properties=False):
        kwargs = {}
        if model in ("service", "workflow_edge"):
            kwargs = {"soft_deleted": False}
        return [
            instance.to_dict(export=True, private_properties=private_properties)
            for instance in self.fetch_all(model, **kwargs)
        ]

    def factory(
        self, _class, commit=False, no_fetch=False, rbac="edit", user=None, **kwargs
    ):
        def transaction(_class, **kwargs):
            property = "path" if _class in ("file", "folder") else "name"
            characters = set(kwargs.get("name", "") + kwargs.get("scoped_name", ""))
            if set("/\\'" + '"') & characters:
                raise ValueError("Names cannot contain a slash or a quote.")
            instance, instance_id = None, kwargs.pop("id", 0)
            if instance_id:
                instance = self.fetch(_class, id=instance_id, rbac=rbac, user=user)
            elif property in kwargs and not no_fetch:
                instance = self.fetch(
                    _class,
                    allow_none=True,
                    rbac=rbac,
                    user=user,
                    **{property: kwargs[property]},
                )
            if instance and not kwargs.get("must_be_new"):
                instance.update(rbac=rbac, **kwargs)
            else:
                instance = vs.models[_class](rbac=rbac, **kwargs)
                self.session.add(instance)
            if "update_source" in kwargs and hasattr(instance, "name"):
                key = f"update_{instance.type}_{instance.name}"
                db.session.connection().info[key] = kwargs["update_source"]
            return instance

        if not commit:
            instance = transaction(_class, **kwargs)
        else:
            instance = self.try_commit(transaction, _class, **kwargs)
        return instance

    def fetch(
        self,
        instance_type,
        allow_none=False,
        all_matches=False,
        properties=None,
        rbac="read",
        user=None,
        **kwargs,
    ):
        query = self.query(instance_type, rbac, user=user, properties=properties)
        if not query:
            return
        query = query.filter(
            *(
                (
                    getattr(vs.models[instance_type], key[:-3]).in_(value)
                    if key.endswith("_in")
                    else getattr(vs.models[instance_type], key) == value
                )
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
                    error(f"Fetch #{index} failed ({format_exc()})")
                    raise exc
                else:
                    warning(f"Fetch #{index} failed ({str(exc)})")
                sleep(self.retry_fetch_time * (index + 1))
        if result or allow_none:
            return result
        else:
            raise self.rbac_error(
                f"There is no {instance_type} in the database with the following "
                f"characteristics: {kwargs}. Either the record does not exist "
                "or the user does not have access"
            )

    def fetch_all(self, instance_type, **kwargs):
        if (
            "name_in" in kwargs
            and not kwargs["name_in"]
            or "id_in" in kwargs
            and not kwargs["id_in"]
        ):
            return []
        return self.fetch(instance_type, allow_none=True, all_matches=True, **kwargs)

    def get_credential(
        self, username, name=None, device=None, credential_type="any", optional=False
    ):
        query = db.query("credential", rbac="use", user=username)
        if device:
            query = query.join(
                vs.models["pool"], vs.models["credential"].device_pools
            ).join(vs.models["device"], vs.models["pool"].devices)
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

    def query(self, model, rbac="read", user=None, properties=None):
        if properties:
            entity = [getattr(vs.models[model], property) for property in properties]
        else:
            entity = [vs.models[model]]
        query = self.session.query(*entity)
        return query

    def register_custom_models(self):
        for model in ("device", "link", "service", "data"):
            folder_name = "datastore" if model == "data" else f"{model}s"
            paths = [vs.path / "eNMS" / "models" / folder_name]
            if vs.settings["paths"][f"custom_{folder_name}"]:
                paths.append(Path(vs.settings["paths"][f"custom_{folder_name}"]))
            for path in paths:
                for file in path.glob("**/*.py"):
                    if "init" in str(file):
                        continue
                    if (
                        "notification" in str(file)
                        and file.stem.split("_")[0] not in vs.automation["notification"]
                    ):
                        continue
                    info(f"Loading {model}: {file}")
                    spec = spec_from_file_location(file.stem, str(file))
                    try:
                        spec.loader.exec_module(module_from_spec(spec))
                    except InvalidRequestError:
                        error(f"Error loading {model} '{file}'\n{format_exc()}")

    def try_commit(self, transaction, *args, **kwargs):
        for index in range(self.retry_commit_number):
            try:
                result = transaction(*args, **kwargs)
                self.session.commit()
                break
            except (AttributeError, ValueError, IntegrityError, self.rbac_error):
                raise
            except Exception as exc:
                self.session.rollback()
                if (
                    index == self.retry_commit_number - 1
                    or isinstance(exc, IntegrityError)
                    and "Duplicate entry" in str(exc)
                    and "for key 'name'" in str(exc)
                ):
                    error(f"Commit #{index + 1} failed ({format_exc()})")
                    raise exc
                else:
                    warning(f"Commit #{index + 1} failed ({str(exc)})")
                sleep(self.retry_commit_time * (index + 1))
        return result

    def try_set(self, instance, property, value):
        def transaction():
            setattr(instance, property, value)

        self.try_commit(transaction)

    @contextmanager
    def session_scope(self, commit=False, remove=False):
        try:
            yield self.session
            if commit:
                self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        finally:
            if remove:
                self.session.remove()

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
                        "".join(word.capitalize() for word in rbac_model.split("_")),
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
        setattr(table, "admin_only", db.Column(Boolean, default=False))
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


db = Database()

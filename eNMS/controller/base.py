from base64 import b64decode, b64encode
from click import get_current_context
from cryptography.fernet import Fernet
from datetime import datetime
from difflib import unified_diff
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from flask_login import current_user
from git import Repo
from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from json import load
from logging.config import dictConfig
from logging import getLogger, error, info
from os import getenv, scandir
from os.path import exists
from pathlib import Path
from re import compile, error as regex_error
from redis import Redis
from redis.exceptions import ConnectionError, TimeoutError
from requests import Session as RequestSession
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from smtplib import SMTP
from string import punctuation
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.orm import aliased, configure_mappers
from sys import path as sys_path
from traceback import format_exc
from uuid import getnode
from warnings import warn

try:
    from hvac import Client as VaultClient
except ImportError as exc:
    warn(f"Couldn't import hvac module ({exc})")

from eNMS.database import db
from eNMS.models import models, model_properties, relationships
from eNMS.controller.syslog import SyslogServer
from eNMS.setup import database, logging, properties, rbac, settings


class BaseController:

    log_levels = ["debug", "info", "warning", "error", "critical"]

    rest_endpoints = [
        "get_cluster_status",
        "get_git_content",
        "update_all_pools",
        "update_database_configurations_from_git",
    ]

    property_names = {}

    def __init__(self):
        self.pre_init()
        self.settings = settings
        self.properties = properties
        self.database = database
        self.logging = logging
        self.cli_command = self.detect_cli()
        self.load_custom_properties()
        self.load_configuration_properties()
        self.path = Path.cwd()
        self.init_rbac()
        self.init_encryption()
        self.use_vault = settings["vault"]["use_vault"]
        if self.use_vault:
            self.init_vault_client()
        if settings["syslog"]["active"]:
            self.init_syslog_server()
        if settings["paths"]["custom_code"]:
            sys_path.append(settings["paths"]["custom_code"])
        self.fetch_version()
        self.init_logs()
        self.init_redis()
        self.init_scheduler()
        self.init_connection_pools()
        self.post_init()

    def init_encryption(self):
        self.fernet_encryption = getenv("FERNET_KEY")
        if self.fernet_encryption:
            fernet = Fernet(self.fernet_encryption)
            self.encrypt, self.decrypt = fernet.encrypt, fernet.decrypt
        else:
            self.encrypt, self.decrypt = b64encode, b64decode

    def detect_cli(self):
        try:
            return get_current_context().info_name == "flask"
        except RuntimeError:
            return False

    def encrypt_password(self, password):
        if isinstance(password, str):
            password = str.encode(password)
        return self.encrypt(password)

    def get_password(self, password):
        if not password:
            return
        if self.fernet_encryption and isinstance(password, str):
            password = str.encode(password)
        return str(self.decrypt(password), "utf-8")

    def initialize_database(self):
        self.init_plugins()
        db.private_properties_list = list(set(sum(db.private_properties.values(), [])))
        self.init_services()
        db.base.metadata.create_all(bind=db.engine)
        configure_mappers()
        db.configure_model_events(self)
        if self.cli_command:
            return
        self.init_forms()
        if not db.fetch("user", allow_none=True, name="admin"):
            self.create_admin_user()
            self.migration_import(
                name=self.settings["app"].get("startup_migration", "default"),
                import_export_types=db.import_export_models,
            )
            self.update_credentials()
            self.get_git_content()
        self.configure_server_id()
        self.reset_run_status()
        db.session.commit()

    def reset_run_status(self):
        for run in db.fetch("run", all_matches=True, allow_none=True, status="Running"):
            run.status = "Aborted (RELOAD)"
            run.service.status = "Idle"
        db.session.commit()

    def fetch_version(self):
        with open(self.path / "package.json") as package_file:
            self.version = load(package_file)["version"]

    def configure_server_id(self):
        db.factory(
            "server",
            **{
                "name": str(getnode()),
                "description": "Localhost",
                "ip_address": "0.0.0.0",
                "status": "Up",
            },
        )

    def create_admin_user(self):
        admin = db.factory("user", name="admin", is_admin=True, commit=True)
        if not admin.password:
            admin.update(password="admin")

    def update_credentials(self):
        with open(self.path / "files" / "spreadsheets" / "usa.xls", "rb") as file:
            self.topology_import(file)

    def get_git_content(self):
        repo = self.settings["app"]["git_repository"]
        if not repo:
            return
        local_path = self.path / "network_data"
        try:
            if exists(local_path):
                Repo(local_path).remotes.origin.pull()
            else:
                local_path.mkdir(parents=True, exist_ok=True)
                Repo.clone_from(repo, local_path)
        except Exception as exc:
            self.log("error", f"Git pull failed ({str(exc)})")
        self.update_database_configurations_from_git()

    def load_custom_properties(self):
        for model, values in self.properties["custom"].items():
            for property, property_dict in values.items():
                pretty_name = property_dict["pretty_name"]
                self.property_names[property] = pretty_name
                model_properties[model].append(property)
                if property_dict.get("private"):
                    if model not in db.private_properties:
                        db.private_properties[model] = []
                    db.private_properties[model].append(property)
                if model == "device" and property_dict.get("configuration"):
                    self.configuration_properties[property] = pretty_name

    def load_configuration_properties(self):
        for property, title in self.configuration_properties.items():
            self.properties["filtering"]["device"].append(property)
            self.properties["tables"]["configuration"].insert(
                -1,
                {
                    "data": property,
                    "title": title,
                    "search": "text",
                    "width": "70%",
                    "visible": property == "configuration",
                    "orderable": False,
                },
            )
            for timestamp in self.configuration_timestamps:
                self.properties["tables"]["configuration"].insert(
                    -1,
                    {
                        "data": f"last_{property}_{timestamp}",
                        "title": f"Last {title} {timestamp.capitalize()}",
                        "search": "text",
                        "visible": False,
                    },
                )

    def init_logs(self):
        folder = self.path / "logs"
        folder.mkdir(parents=True, exist_ok=True)
        with open(self.path / "setup" / "logging.json", "r") as logging_config:
            logging_config = load(logging_config)
        dictConfig(logging_config)
        for logger, log_level in logging_config["external_loggers"].items():
            info(f"Changing {logger} log level to '{log_level}'")
            log_level = getattr(import_module("logging"), log_level.upper())
            getLogger(logger).setLevel(log_level)

    def init_connection_pools(self):
        self.request_session = RequestSession()
        retry = Retry(**self.settings["requests"]["retries"])
        for protocol in ("http", "https"):
            self.request_session.mount(
                f"{protocol}://",
                HTTPAdapter(max_retries=retry, **self.settings["requests"]["pool"]),
            )

    def init_forms(self):
        for file in (self.path / "eNMS" / "forms").glob("**/*.py"):
            spec = spec_from_file_location(str(file).split("/")[-1][:-3], str(file))
            spec.loader.exec_module(module_from_spec(spec))

    def init_rbac(self):
        self.rbac = {"pages": [], **rbac}
        for _, category in rbac["menu"].items():
            for page, page_values in category["pages"].items():
                if page_values["rbac"] == "access":
                    self.rbac["pages"].append(page)
                for subpage, subpage_values in page_values.get("subpages", {}).items():
                    if subpage_values["rbac"] == "access":
                        self.rbac["pages"].append(subpage)

    def init_redis(self):
        host = getenv("REDIS_ADDR")
        self.redis_queue = (
            Redis(
                host=host,
                port=6379,
                db=0,
                charset="utf-8",
                decode_responses=True,
                socket_timeout=0.1,
            )
            if host
            else None
        )

    def init_scheduler(self):
        self.scheduler_address = getenv("SCHEDULER_ADDR")

    def update_settings(self, old, new):
        for key, value in new.items():
            if key not in old:
                old[key] = value
            else:
                old_value = old[key]
                if isinstance(old_value, list):
                    old_value.extend(value)
                elif isinstance(old_value, dict):
                    self.update_settings(old_value, value)
                else:
                    old[key] = value

        return old

    def init_plugins(self):
        self.plugins = {}
        for plugin_path in Path(self.settings["app"]["plugin_path"]).iterdir():
            if not Path(plugin_path / "settings.json").exists():
                continue
            try:
                with open(plugin_path / "settings.json", "r") as file:
                    settings = load(file)
                if not settings["active"]:
                    continue
                self.plugins[plugin_path.stem] = {
                    "settings": settings,
                    "module": import_module(f"eNMS.plugins.{plugin_path.stem}"),
                }
                for setup_file in ("database", "properties", "rbac"):
                    property = getattr(self, setup_file)
                    self.update_settings(property, settings.get(setup_file, {}))
            except Exception as exc:
                error(f"Could not load plugin '{plugin_path.stem}' ({exc})")
                continue
            info(f"Loading plugin: {settings['name']}")

    def init_services(self):
        path_services = [self.path / "eNMS" / "services"]
        load_examples = self.settings["app"].get("startup_migration") == "examples"
        if self.settings["paths"]["custom_services"]:
            path_services.append(Path(self.settings["paths"]["custom_services"]))
        for path in path_services:
            for file in path.glob("**/*.py"):
                if "init" in str(file):
                    continue
                if not load_examples and "examples" in str(file):
                    continue
                info(f"Loading service: {file}")
                spec = spec_from_file_location(file.stem, str(file))
                try:
                    spec.loader.exec_module(module_from_spec(spec))
                except InvalidRequestError as exc:
                    error(f"Error loading custom service '{file}' ({str(exc)})")

    def init_vault_client(self):
        url = getenv("VAULT_ADDR", "http://127.0.0.1:8200")
        self.vault_client = VaultClient(url=url, token=getenv("VAULT_TOKEN"))
        if self.vault_client.sys.is_sealed() and self.settings["vault"]["unseal_vault"]:
            keys = [getenv(f"UNSEAL_VAULT_KEY{i}") for i in range(1, 6)]
            self.vault_client.sys.submit_unseal_keys(filter(None, keys))

    def init_syslog_server(self):
        self.syslog_server = SyslogServer(
            self.settings["syslog"]["address"], self.settings["syslog"]["port"]
        )
        self.syslog_server.start()

    def redis(self, operation, *args, **kwargs):
        try:
            return getattr(self.redis_queue, operation)(*args, **kwargs)
        except (ConnectionError, TimeoutError) as exc:
            self.log("error", f"Redis Queue Unreachable ({exc})", change_log=False)

    def log_queue(self, runtime, service, log=None, mode="add", start_line=0):
        if self.redis_queue:
            key = f"{runtime}/{service}/logs"
            self.run_logs[runtime][int(service)] = None
            if mode == "add":
                log = self.redis("lpush", key, log)
            else:
                log = self.redis("lrange", key, 0, -1)
                if log:
                    log = log[::-1][start_line:]
        else:
            if mode == "add":
                return self.run_logs[runtime][int(service)].append(log)
            else:
                full_log = getattr(self.run_logs[runtime], mode)(int(service), [])
                log = full_log[start_line:]
        return log

    def delete_instance(self, model, instance_id):
        return db.delete(model, id=instance_id)

    def get(self, model, id):
        return db.fetch(model, id=id).serialized

    def get_properties(self, model, id):
        return db.fetch(model, id=id).get_properties()

    def get_all(self, model):
        return [instance.get_properties() for instance in db.fetch_all(model)]

    def update(self, type, **kwargs):
        try:
            kwargs.update(
                {
                    "last_modified": self.get_time(),
                    "update_pools": True,
                    "must_be_new": kwargs.get("id") == "",
                }
            )
            for arg in ("name", "scoped_name"):
                if arg in kwargs:
                    kwargs[arg] = kwargs[arg].strip()
            if kwargs["must_be_new"]:
                kwargs["creator"] = kwargs["user"] = getattr(current_user, "name", "")
            instance = db.factory(type, **kwargs)
            if kwargs.get("copy"):
                db.fetch(type, id=kwargs["copy"]).duplicate(clone=instance)
            db.session.flush()
            return instance.serialized
        except db.rbac_error:
            return {"alert": "Error 403 - Operation not allowed."}
        except Exception as exc:
            db.session.rollback()
            if isinstance(exc, IntegrityError):
                return {"alert": f"There is already a {type} with the same parameters."}
            self.log("error", format_exc())
            return {"alert": str(exc)}

    def log(self, severity, content, user=None, change_log=True, logger="root"):
        logger_settings = self.logging["loggers"].get(logger, {})
        if logger:
            getattr(getLogger(logger), severity)(content)
        if change_log or logger and logger_settings.get("change_log"):
            db.factory(
                "changelog",
                **{
                    "severity": severity,
                    "content": content,
                    "user": user or getattr(current_user, "name", ""),
                },
            )
        return logger_settings

    def compare(self, type, id, v1, v2, context_lines):
        if type in ("result", "device_result"):
            first = self.str_dict(getattr(db.fetch("result", id=v1), "result"))
            second = self.str_dict(getattr(db.fetch("result", id=v2), "result"))
        else:
            device = db.fetch("device", id=id)
            result1, v1 = self.get_git_network_data(device.name, v1)
            result2, v2 = self.get_git_network_data(device.name, v2)
            first, second = result1[type], result2[type]
        return "\n".join(
            unified_diff(
                first.splitlines(),
                second.splitlines(),
                fromfile=f"V1 ({v1})",
                tofile=f"V2 ({v2})",
                lineterm="",
                n=int(context_lines),
            )
        )

    def build_filtering_constraints(self, model, **kwargs):
        table, constraints = models[model], []
        constraint_dict = {**kwargs["form"], **kwargs.get("constraints", {})}
        for property in model_properties[model]:
            value = constraint_dict.get(property)
            if not value:
                continue
            filter_value = constraint_dict.get(f"{property}_filter")
            if value in ("bool-true", "bool-false"):
                constraint = getattr(table, property) == (value == "bool-true")
            elif filter_value == "equality":
                constraint = getattr(table, property) == value
            elif (
                not filter_value
                or filter_value == "inclusion"
                or db.dialect == "sqlite"
            ):
                constraint = getattr(table, property).contains(
                    value, autoescape=isinstance(value, str)
                )
            else:
                compile(value)
                regex_operator = "regexp" if db.dialect == "mysql" else "~"
                constraint = getattr(table, property).op(regex_operator)(value)
            constraints.append(constraint)
        return constraints

    def multiselect_filtering(self, model, **params):
        table = models[model]
        results = db.query(model).filter(table.name.contains(params.get("term")))
        return {
            "items": [
                {"text": result.ui_name, "id": str(result.id)}
                for result in results.limit(10)
                .offset((int(params["page"]) - 1) * 10)
                .all()
            ],
            "total_count": results.count(),
        }

    def build_relationship_constraints(self, query, model, **kwargs):
        table = models[model]
        constraint_dict = {**kwargs["form"], **kwargs.get("constraints", {})}
        for related_model, relation_properties in relationships[model].items():
            relation_ids = [int(id) for id in constraint_dict.get(related_model, [])]
            if not relation_ids:
                continue
            related_table = aliased(models[relation_properties["model"]])
            query = query.join(related_table, getattr(table, related_model)).filter(
                related_table.id.in_(relation_ids)
            )
        return query

    def filtering(self, model, bulk=False, **kwargs):
        table, query = models[model], db.query(model)
        total_records = query.with_entities(table.id).count()
        try:
            constraints = self.build_filtering_constraints(model, **kwargs)
        except regex_error:
            return {"error": "Invalid regular expression as search parameter."}
        constraints.extend(table.filtering_constraints(**kwargs))
        query = self.build_relationship_constraints(query, model, **kwargs)
        query = query.filter(and_(*constraints))
        filtered_records = query.with_entities(table.id).count()
        if bulk:
            instances = query.all()
            return instances if bulk == "object" else [obj.id for obj in instances]
        data = kwargs["columns"][int(kwargs["order"][0]["column"])]["data"]
        ordering = getattr(getattr(table, data, None), kwargs["order"][0]["dir"], None)
        if ordering:
            query = query.order_by(ordering())
        table_result = {
            "draw": int(kwargs["draw"]),
            "recordsTotal": total_records,
            "recordsFiltered": filtered_records,
            "data": [
                obj.table_properties(**kwargs)
                for obj in query.limit(int(kwargs["length"]))
                .offset(int(kwargs["start"]))
                .all()
            ],
        }
        if kwargs.get("export"):
            table_result["full_result"] = [
                obj.table_properties(**kwargs) for obj in query.all()
            ]
        if kwargs.get("clipboard"):
            table_result["full_result"] = ",".join(obj.name for obj in query.all())
        return table_result

    def allowed_file(self, name, allowed_modules):
        allowed_syntax = "." in name
        allowed_extension = name.rsplit(".", 1)[1].lower() in allowed_modules
        return allowed_syntax and allowed_extension

    def bulk_deletion(self, table, **kwargs):
        instances = self.filtering(table, bulk=True, form=kwargs)
        for instance_id in instances:
            db.delete(table, id=instance_id)
        return len(instances)

    def bulk_edit(self, table, **kwargs):
        instances = kwargs.pop("id").split("-")
        kwargs = {
            property: value
            for property, value in kwargs.items()
            if kwargs.get(f"bulk-edit-{property}")
        }
        for instance_id in instances:
            db.factory(table, id=instance_id, **kwargs)
        return len(instances)

    def get_time(self):
        return str(datetime.now())

    def remove_instance(self, **kwargs):
        instance = db.fetch(kwargs["instance"]["type"], id=kwargs["instance"]["id"])
        target = db.fetch(kwargs["relation"]["type"], id=kwargs["relation"]["id"])
        if target.type == "pool" and not target.manually_defined:
            return {"alert": "Removing an object from a dynamic pool is an allowed."}
        getattr(target, kwargs["relation"]["relation"]["to"]).remove(instance)
        self.update_rbac(instance)

    def add_instances_in_bulk(self, **kwargs):
        target = db.fetch(kwargs["relation_type"], id=kwargs["relation_id"])
        if target.type == "pool" and not target.manually_defined:
            return {"alert": "Adding objects to a dynamic pool is not allowed."}
        model, property = kwargs["model"], kwargs["property"]
        instances = set(db.objectify(model, kwargs["instances"]))
        if kwargs["names"]:
            for name in [instance.strip() for instance in kwargs["names"].split(",")]:
                instance = db.fetch(model, allow_none=True, name=name)
                if not instance:
                    return {"alert": f"{model.capitalize()} '{name}' does not exist."}
                instances.add(instance)
        instances = instances - set(getattr(target, property))
        for instance in instances:
            getattr(target, property).append(instance)
        target.last_modified = self.get_time()
        self.update_rbac(*instances)
        return {"number": len(instances), "target": target.base_properties}

    def bulk_removal(
        self,
        table,
        target_type,
        target_id,
        target_property,
        constraint_property,
        **kwargs,
    ):
        kwargs[constraint_property] = [target_id]
        target = db.fetch(target_type, id=target_id)
        if target.type == "pool" and not target.manually_defined:
            return {"alert": "Removing objects from a dynamic pool is an allowed."}
        instances = self.filtering(table, bulk="object", form=kwargs)
        for instance in instances:
            getattr(target, target_property).remove(instance)
        self.update_rbac(*instances)
        return len(instances)

    def update_rbac(self, *instances):
        for instance in instances:
            if instance.type != "user":
                continue
            instance.update_rbac()

    def send_email(
        self,
        subject,
        content,
        recipients="",
        reply_to=None,
        sender=None,
        filename=None,
        file_content=None,
    ):
        sender = sender or self.settings["mail"]["sender"]
        message = MIMEMultipart()
        message["From"] = sender
        message["To"] = recipients
        message["Date"] = formatdate(localtime=True)
        message["Subject"] = subject
        message.add_header("reply-to", reply_to or self.settings["mail"]["reply_to"])
        message.attach(MIMEText(content))
        if filename:
            attached_file = MIMEApplication(file_content, Name=filename)
            attached_file["Content-Disposition"] = f'attachment; filename="{filename}"'
            message.attach(attached_file)
        server = SMTP(self.settings["mail"]["server"], self.settings["mail"]["port"])
        if self.settings["mail"]["use_tls"]:
            server.starttls()
            password = getenv("MAIL_PASSWORD", "")
            server.login(self.settings["mail"]["username"], password)
        server.sendmail(sender, recipients.split(","), message.as_string())
        server.close()

    def contains_set(self, input):
        if isinstance(input, set):
            return True
        elif isinstance(input, list):
            return any(self.contains_set(x) for x in input)
        elif isinstance(input, dict):
            return any(self.contains_set(x) for x in input.values())
        else:
            return False

    def str_dict(self, input, depth=0):
        tab = "\t" * depth
        if isinstance(input, list):
            result = "\n"
            for element in input:
                result += f"{tab}- {self.str_dict(element, depth + 1)}\n"
            return result
        elif isinstance(input, dict):
            result = ""
            for key, value in input.items():
                result += f"\n{tab}{key}: {self.str_dict(value, depth + 1)}"
            return result
        else:
            return str(input)

    def strip_all(self, input):
        return input.translate(str.maketrans("", "", f"{punctuation} "))

    def update_database_configurations_from_git(self):
        for dir in scandir(self.path / "network_data"):
            device = db.fetch("device", allow_none=True, name=dir.name)
            timestamp_path = Path(dir.path) / "timestamps.json"
            if not device:
                continue
            try:
                with open(timestamp_path) as file:
                    timestamps = load(file)
            except Exception:
                timestamps = {}
            for property in self.configuration_properties:
                for timestamp, value in timestamps.get(property, {}).items():
                    setattr(device, f"last_{property}_{timestamp}", value)
                filepath = Path(dir.path) / property
                if not filepath.exists():
                    continue
                with open(filepath) as file:
                    setattr(device, property, file.read())
        db.session.commit()
        for pool in db.fetch_all("pool"):
            if any(
                getattr(pool, f"device_{property}")
                for property in self.configuration_properties
            ):
                pool.compute_pool()

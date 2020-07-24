from base64 import b64decode, b64encode
from collections import Counter
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
from os import environ, scandir
from os.path import exists
from pathlib import Path
from re import compile, error as regex_error
from redis import Redis
from redis.exceptions import ConnectionError, TimeoutError
from requests import Session as RequestSession
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from ruamel import yaml
from smtplib import SMTP
from string import punctuation
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.orm import configure_mappers
from sys import path as sys_path
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
        self.settings = settings
        self.rbac = rbac
        self.properties = properties
        self.database = database
        self.logging = logging
        self.load_custom_properties()
        self.path = Path.cwd()
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

    def init_encryption(self):
        self.fernet_encryption = environ.get("FERNET_KEY")
        if self.fernet_encryption:
            fernet = Fernet(self.fernet_encryption)
            self.encrypt, self.decrypt = fernet.encrypt, fernet.decrypt
        else:
            self.encrypt, self.decrypt = b64encode, b64decode

    def get_password(self, password):
        if not password:
            return
        if self.fernet_encryption and isinstance(password, str):
            password = str.encode(password)
        return str(self.decrypt(password), "utf-8")

    def initialize_database(self):
        self.init_services()
        db.base.metadata.create_all(bind=db.engine)
        configure_mappers()
        db.configure_application_events(self)
        self.init_forms()
        if not db.fetch("user", allow_none=True, name="admin"):
            self.create_admin_user()
            db.session.commit()
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
        admin = db.factory("user", name="admin", is_admin=True)
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
                    db.private_properties.append(property)
                if model == "device" and property_dict.get("configuration"):
                    self.configuration_properties[property] = pretty_name

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

    def init_redis(self):
        host = environ.get("REDIS_ADDR")
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
        self.scheduler_address = environ.get("SCHEDULER_ADDR")

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
                spec = spec_from_file_location(str(file).split("/")[-1][:-3], str(file))
                try:
                    spec.loader.exec_module(module_from_spec(spec))
                except InvalidRequestError as exc:
                    error(f"Error loading custom service '{file}' ({str(exc)})")

    def init_vault_client(self):
        url = environ.get("VAULT_ADDR", "http://127.0.0.1:8200")
        self.vault_client = VaultClient(url=url, token=environ.get("VAULT_TOKEN"))
        if self.vault_client.sys.is_sealed() and self.settings["vault"]["unseal_vault"]:
            keys = [environ.get(f"UNSEAL_VAULT_KEY{i}") for i in range(1, 6)]
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

    def log_queue(self, runtime, service, log=None, mode="add"):
        if self.redis_queue:
            key = f"{runtime}/{service}/logs"
            self.run_logs[runtime][int(service)] = None
            if mode == "add":
                log = self.redis("lpush", key, log)
            else:
                log = self.redis("lrange", key, 0, -1)
                if log:
                    log = log[::-1]
        else:
            if mode == "add":
                return self.run_logs[runtime][int(service)].append(log)
            else:
                log = getattr(self.run_logs[runtime], mode)(int(service), [])
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
            must_be_new = kwargs.get("id") == ""
            for arg in ("name", "scoped_name"):
                if arg in kwargs:
                    kwargs[arg] = kwargs[arg].strip()
            kwargs["last_modified"] = self.get_time()
            kwargs["creator"] = kwargs["user"] = getattr(current_user, "name", "")
            instance = db.factory(type, must_be_new=must_be_new, **kwargs)
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
                    "user": user or getattr(current_user, "name", "admin"),
                },
            )
        return logger_settings

    def count_models(self):
        return {
            "counters": {
                model: db.query(model).count() for model in properties["dashboard"]
            },
            "properties": {
                model: Counter(
                    str(getattr(instance, properties["dashboard"][model][0]))
                    for instance in db.fetch_all(model)
                )
                for model in properties["dashboard"]
            },
        }

    def compare(self, type, device_name, v1, v2):
        if type in ("result", "device_result"):
            first = self.str_dict(getattr(db.fetch("result", id=v1), "result"))
            second = self.str_dict(getattr(db.fetch("result", id=v2), "result"))
        else:
            first = self.get_git_network_data(device_name, v1)[type]
            second = self.get_git_network_data(device_name, v2)[type]
        return "\n".join(
            unified_diff(
                first.splitlines(),
                second.splitlines(),
                fromfile="-",
                tofile="-",
                lineterm="",
            )
        )

    def build_filtering_constraints(self, model, **kwargs):
        table, constraints = models[model], []
        for property in model_properties[model]:
            value = kwargs["form"].get(property)
            if not value:
                continue
            filter = kwargs["form"].get(f"{property}_filter")
            if value in ("bool-true", "bool-false"):
                constraint = getattr(table, property) == (value == "bool-true")
            elif filter == "equality":
                constraint = getattr(table, property) == value
            elif not filter or filter == "inclusion" or db.dialect == "sqlite":
                constraint = getattr(table, property).contains(value)
            else:
                compile(value)
                regex_operator = "regexp" if db.dialect == "mysql" else "~"
                constraint = getattr(table, property).op(regex_operator)(value)
            constraints.append(constraint)
        for related_model, relation_properties in relationships[model].items():
            relation_ids = [int(id) for id in kwargs["form"].get(related_model, [])]
            filter = kwargs["form"].get(f"{related_model}_filter")
            if filter == "none":
                constraint = ~getattr(table, related_model).any()
            elif not relation_ids:
                continue
            elif relation_properties["list"]:
                constraint = (and_ if filter == "all" else or_)(
                    getattr(table, related_model).any(id=relation_id)
                    for relation_id in relation_ids
                )
                if filter == "not_any":
                    constraint = ~constraint
            else:
                constraint = or_(
                    getattr(table, related_model).has(id=relation_id)
                    for relation_id in relation_ids
                )
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

    def filtering(self, model, **kwargs):
        table = models[model]
        ordering = getattr(
            getattr(
                table,
                kwargs["columns"][int(kwargs["order"][0]["column"])]["data"],
                None,
            ),
            kwargs["order"][0]["dir"],
            None,
        )
        try:
            constraints = self.build_filtering_constraints(model, **kwargs)
        except regex_error:
            return {"error": "Invalid regular expression as search parameter."}
        constraints.extend(table.filtering_constraints(**kwargs))
        query = db.query(model)
        total_records, query = query.count(), query.filter(and_(*constraints))
        if ordering:
            query = query.order_by(ordering())
        table_result = {
            "draw": int(kwargs["draw"]),
            "recordsTotal": total_records,
            "recordsFiltered": query.count(),
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
        return table_result

    def allowed_file(self, name, allowed_modules):
        allowed_syntax = "." in name
        allowed_extension = name.rsplit(".", 1)[1].lower() in allowed_modules
        return allowed_syntax and allowed_extension

    def get_time(self):
        return str(datetime.now())

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
            password = environ.get("MAIL_PASSWORD", "")
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
            if not device:
                continue
            with open(Path(dir.path) / "data.yml") as data:
                parameters = yaml.load(data)
                device.update(**{"dont_update_pools": True, **parameters})
            for data in self.configuration_properties:
                filepath = Path(dir.path) / data
                if not filepath.exists():
                    continue
                with open(filepath) as file:
                    setattr(device, data, file.read())
        db.session.commit()
        for pool in db.fetch_all("pool"):
            if any(
                getattr(pool, f"device_{property}")
                for property in self.configuration_properties
            ):
                pool.compute_pool()

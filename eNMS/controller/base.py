from apscheduler.schedulers.background import BackgroundScheduler
from collections import Counter
from datetime import datetime
from difflib import SequenceMatcher
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from flask_login import current_user
from git import Repo
from hvac import Client as VaultClient
from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from json import load
from ldap3 import ALL, Server
from logging import basicConfig, error, info, StreamHandler, warning
from logging.handlers import RotatingFileHandler
from os import environ, scandir
from os.path import exists
from pathlib import Path
from requests import Session as RequestSession
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from ruamel import yaml
from smtplib import SMTP
from string import punctuation
from sqlalchemy import and_, func, or_
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.orm import configure_mappers
from sys import path as sys_path
from tacacs_plus.client import TACACSClient
from uuid import getnode

from eNMS.settings import settings, table_properties
from eNMS.database import Base, DIALECT, engine, Session
from eNMS.database.events import configure_events
from eNMS.database.functions import (
    count,
    delete,
    factory,
    fetch,
    fetch_all,
    get_query_count,
)
from eNMS.models import models, model_properties, relationships
from eNMS.properties import private_properties, property_names
from eNMS.properties.database import import_classes
from eNMS.properties.diagram import (
    device_diagram_properties,
    type_to_diagram_properties,
)
from eNMS.properties.objects import (
    device_properties,
    pool_device_properties,
)
from eNMS.controller.syslog import SyslogServer
from eNMS.settings import dashboard_properties


class BaseController:

    log_severity = {"error": error, "info": info, "warning": warning}

    get_endpoints = [
        "/dashboard",
        "/login",
        "/table/changelog",
        "/table/device",
        "/table/event",
        "/table/pool",
        "/table/link",
        "/table/run",
        "/table/server",
        "/table/service",
        "/table/task",
        "/table/user",
        "/view/network",
        "/view/site",
        "/workflow_builder",
    ]

    json_endpoints = [
        "get_configuration_context",
        "multiselect_filtering",
        "save_settings",
        "table_filtering",
        "view_filtering",
    ]

    form_endpoints = [
        "add_edge",
        "add_service_to_workflow",
        "copy_service_in_workflow",
        "calendar_init",
        "clear_results",
        "clear_configurations",
        "compare",
        "connection",
        "counters",
        "count_models",
        "create_label",
        "database_deletion",
        "delete_edge",
        "delete_instance",
        "delete_label",
        "delete_node",
        "duplicate_workflow",
        "export_service",
        "export_topology",
        "delete_file",
        "edit_file",
        "get",
        "get_all",
        "get_cluster_status",
        "get_configuration_context",
        "get_device_network_data",
        "get_device_logs",
        "get_exported_services",
        "get_git_content",
        "get_migration_folders",
        "get_service_logs",
        "get_properties",
        "get_result",
        "get_runtimes",
        "get_view_topology",
        "get_service_state",
        "get_session_log",
        "get_top_level_workflows",
        "get_tree_files",
        "get_workflow_results",
        "get_workflow_services",
        "handoffssh",
        "import_service",
        "import_topology",
        "migration_export",
        "migration_import",
        "reset_status",
        "run_service",
        "save_file",
        "save_parameters",
        "save_pool_objects",
        "save_positions",
        "scan_cluster",
        "scan_playbook_folder",
        "scheduler",
        "skip_services",
        "stop_workflow",
        "switch_menu",
        "scheduler_action",
        "task_action",
        "topology_import",
        "update",
        "update_parameters",
        "update_pool",
        "update_all_pools",
        "upload_files",
    ]

    rest_endpoints = [
        "get_cluster_status",
        "get_git_content",
        "update_all_pools",
        "update_database_configurations_from_git",
    ]

    def __init__(self):
        self.settings = settings
        self.table_properties = table_properties
        self.path = Path.cwd()
        self.custom_properties = self.load_custom_properties()
        self.init_scheduler()
        if settings["tacacs"]["active"]:
            self.init_tacacs_client()
        if settings["ldap"]["active"]:
            self.init_ldap_client()
        if settings["vault"]["active"]:
            self.init_vault_client()
        if settings["syslog"]["active"]:
            self.init_syslog_server()
        if settings["paths"]["custom_code"]:
            sys_path.append(settings["paths"]["custom_code"])
        self.fetch_version()
        self.init_logs()
        self.init_connection_pools()

    def configure_database(self):
        self.init_services()
        Base.metadata.create_all(bind=engine)
        configure_mappers()
        configure_events(self)
        self.init_forms()
        self.clean_database()
        if not fetch("user", allow_none=True, name="admin"):
            self.configure_server_id()
            self.create_admin_user()
            Session.commit()
            if self.settings["app"]["create_examples"]:
                self.migration_import(
                    name="examples", import_export_types=import_classes
                )
                self.update_credentials()
            else:
                self.migration_import(
                    name="default", import_export_types=import_classes
                )
            self.get_git_content()
            Session.commit()

    def clean_database(self):
        for run in fetch("run", all_matches=True, allow_none=True, status="Running"):
            run.status = "Aborted (app reload)"
        Session.commit()

    def fetch_version(self):
        with open(self.path / "package.json") as package_file:
            self.version = load(package_file)["version"]

    def configure_server_id(self):
        factory(
            "server",
            **{
                "name": str(getnode()),
                "description": "Localhost",
                "ip_address": "0.0.0.0",
                "status": "Up",
            },
        )

    def create_admin_user(self) -> None:
        admin = factory("user", **{"name": "admin"})
        if not admin.password:
            admin.password = "admin"

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
        filepath = self.settings["paths"]["custom_properties"]
        if not filepath:
            custom_properties = {}
        else:
            with open(filepath, "r") as properties:
                custom_properties = yaml.load(properties)
        property_names.update(
            {k: v["pretty_name"] for k, v in custom_properties.items()}
        )
        public_custom_properties = {
            k: v for k, v in custom_properties.items() if not v.get("private", False)
        }
        device_properties.extend(list(custom_properties))
        pool_device_properties.extend(list(public_custom_properties))
        model_properties["device"].extend(list(public_custom_properties))
        device_diagram_properties.extend(
            list(p for p, v in custom_properties.items() if v["add_to_dashboard"])
        )
        private_properties.extend(
            list(p for p, v in custom_properties.items() if v.get("private", False))
        )
        return custom_properties

    def init_logs(self):
        log_level = self.settings["app"]["log_level"].upper()
        folder = self.path / "logs"
        folder.mkdir(parents=True, exist_ok=True)
        basicConfig(
            level=getattr(import_module("logging"), log_level),
            format="%(asctime)s %(levelname)-8s %(message)s",
            datefmt="%m-%d-%Y %H:%M:%S",
            handlers=[
                RotatingFileHandler(
                    folder / "enms.log", maxBytes=20_000_000, backupCount=10
                ),
                StreamHandler(),
            ],
        )

    def init_connection_pools(self):
        self.request_session = RequestSession()
        retry = Retry(**self.settings["requests"]["retries"])
        for protocol in ("http", "https"):
            self.request_session.mount(
                f"{protocol}://",
                HTTPAdapter(max_retries=retry, **self.settings["requests"]["pool"],),
            )

    def init_scheduler(self):
        self.scheduler = BackgroundScheduler(
            {
                "apscheduler.jobstores.default": {
                    "type": "sqlalchemy",
                    "url": "sqlite:///jobs.sqlite",
                },
                "apscheduler.executors.default": {
                    "class": "apscheduler.executors.pool:ThreadPoolExecutor",
                    "max_workers": "50",
                },
                "apscheduler.job_defaults.misfire_grace_time": "5",
                "apscheduler.job_defaults.coalesce": "true",
                "apscheduler.job_defaults.max_instances": "3",
            }
        )
        self.scheduler.start()

    def init_forms(self):
        for file in (self.path / "eNMS" / "forms").glob("**/*.py"):
            spec = spec_from_file_location(str(file).split("/")[-1][:-3], str(file))
            spec.loader.exec_module(module_from_spec(spec))

    def init_services(self):
        path_services = [self.path / "eNMS" / "services"]
        if self.settings["paths"]["custom_services"]:
            path_services.append(Path(self.settings["paths"]["custom_services"]))
        for path in path_services:
            for file in path.glob("**/*.py"):
                if "init" in str(file):
                    continue
                if not self.settings["app"]["create_examples"] and "examples" in str(
                    file
                ):
                    continue
                info(f"Loading service: {file}")
                spec = spec_from_file_location(str(file).split("/")[-1][:-3], str(file))
                try:
                    spec.loader.exec_module(module_from_spec(spec))
                except InvalidRequestError as e:
                    error(f"Error loading custom service '{file}' ({str(e)})")

    def init_ldap_client(self):
        self.ldap_client = Server(self.settings["ldap"]["server"], get_info=ALL)

    def init_tacacs_client(self):
        self.tacacs_client = TACACSClient(
            self.settings["tacacs"]["address"], 49, environ.get("TACACS_PASSWORD")
        )

    def init_vault_client(self):
        self.vault_client = VaultClient()
        self.vault_client.token = environ.get("VAULT_TOKEN")
        if self.vault_client.sys.is_sealed() and self.settings["vault"]["unseal"]:
            keys = [environ.get(f"UNSEAL_VAULT_KEY{i}") for i in range(1, 6)]
            self.vault_client.sys.submit_unseal_keys(filter(None, keys))

    def init_syslog_server(self):
        self.syslog_server = SyslogServer(
            self.settings["syslog"]["address"], self.settings["syslog"]["port"]
        )
        self.syslog_server.start()

    def update_parameters(self, **kwargs):
        Session.query(models["parameters"]).one().update(**kwargs)
        self.__dict__.update(**kwargs)

    def delete_instance(self, instance_type, instance_id):
        return delete(instance_type, id=instance_id)

    def get(self, instance_type, id):
        return fetch(instance_type, id=id).serialized

    def get_properties(self, instance_type, id):
        return fetch(instance_type, id=id).get_properties()

    def get_all(self, instance_type):
        return [instance.get_properties() for instance in fetch_all(instance_type)]

    def update(self, instance_type, **kwargs):
        try:
            must_be_new = kwargs.get("id") == ""
            for arg in ("name", "scoped_name"):
                if arg in kwargs:
                    kwargs[arg] = kwargs[arg].strip()
            kwargs["last_modified"] = self.get_time()
            kwargs["creator"] = kwargs["user"] = getattr(current_user, "name", "admin")
            instance = factory(instance_type, must_be_new=must_be_new, **kwargs)
            if kwargs.get("original"):
                fetch(instance_type, id=kwargs["original"]).duplicate(clone=instance)
            Session.flush()
            return instance.serialized
        except Exception as exc:
            Session.rollback()
            if isinstance(exc, IntegrityError):
                return {
                    "alert": (f"There already is a {instance_type} with the same name")
                }
            return {"alert": str(exc)}

    def log(self, severity, content):
        factory(
            "changelog",
            **{
                "severity": severity,
                "content": content,
                "user": getattr(current_user, "name", "admin"),
            },
        )
        self.log_severity[severity](content)

    def count_models(self):
        return {
            "counters": {
                instance_type: count(instance_type) for instance_type in dashboard_properties
            },
            "properties": {
                instance_type: Counter(
                    str(getattr(instance, type_to_diagram_properties[instance_type][0]))
                    for instance in fetch_all(instance_type)
                )
                for instance_type in dashboard_properties
            },
        }

    def compare(self, type, result1, result2):
        first = self.str_dict(getattr(fetch(type, id=result1), "result")).splitlines()
        second = self.str_dict(getattr(fetch(type, id=result2), "result")).splitlines()
        opcodes = SequenceMatcher(None, first, second).get_opcodes()
        return {"first": first, "second": second, "opcodes": opcodes}

    def build_filtering_constraints(self, obj_type, **kwargs):
        model, constraints = models[obj_type], []
        for property in model_properties[obj_type]:
            value = kwargs["form"].get(property)
            if not value:
                continue
            filter = kwargs["form"].get(f"{property}_filter")
            print(kwargs["form"])
            if value in ("bool-true", "bool-false"):
                constraint = getattr(model, property) == (value == "bool-true")
            elif filter == "equality":
                constraint = getattr(model, property) == value
            elif not filter or filter == "inclusion" or DIALECT == "sqlite":
                constraint = getattr(model, property).contains(value)
            else:
                regex_operator = "regexp" if DIALECT == "mysql" else "~"
                constraint = getattr(model, property).op(regex_operator)(value)
            constraints.append(constraint)
        for related_model, relation_properties in relationships[obj_type].items():
            relation_ids = [int(id) for id in kwargs["form"].get(related_model, [])]
            filter = kwargs["form"].get(f"{related_model}_filter")
            if filter == "none":
                constraint = ~getattr(model, related_model).any()
            elif not relation_ids:
                continue
            elif relation_properties["list"]:
                constraint = getattr(model, related_model).any(
                    models[relation_properties["model"]].id.in_(relation_ids)
                )
                if filter == "not_any":
                    constraint = ~constraint
            else:
                constraint = or_(
                    getattr(model, related_model).has(id=relation_id)
                    for relation_id in relation_ids
                )
            constraints.append(constraint)
        return constraints

    def multiselect_filtering(self, type, **params):
        model = models[type]
        results = Session.query(model).filter(model.name.contains(params.get("term")))
        return {
            "items": [
                {"text": result.ui_name, "id": str(result.id)}
                for result in results.limit(10)
                .offset((int(params["page"]) - 1) * 10)
                .all()
            ],
            "total_count": results.count(),
        }

    def table_filtering(self, table, **kwargs):
        model = models[table]
        ordering = getattr(
            getattr(
                model,
                kwargs["columns"][int(kwargs["order"][0]["column"])]["data"],
                None,
            ),
            kwargs["order"][0]["dir"],
            None,
        )
        constraints = self.build_filtering_constraints(table, **kwargs)
        if table == "result":
            constraints.append(
                getattr(
                    models["result"],
                    "device" if kwargs["instance"]["type"] == "device" else "service",
                ).has(id=kwargs["instance"]["id"])
            )
            if kwargs.get("runtime"):
                constraints.append(models["result"].parent_runtime == kwargs["runtime"])
        if table == "service":
            workflow_id = kwargs["form"].get("workflow-filtering")
            if workflow_id:
                constraints.append(
                    models["service"].workflows.any(
                        models["workflow"].id == int(workflow_id)
                    )
                )
            else:
                if kwargs["form"].get("parent-filtering", "true") == "true":
                    constraints.append(~models["service"].workflows.any())
        if table == "run":
            constraints.append(models["run"].parent_runtime == models["run"].runtime)
        result = Session.query(model).filter(and_(*constraints))
        if ordering:
            result = result.order_by(ordering())
        return {
            "draw": int(kwargs["draw"]),
            "recordsTotal": Session.query(func.count(model.id)).scalar(),
            "recordsFiltered": get_query_count(result),
            "data": [
                obj.table_properties(**kwargs)
                for obj in result.limit(int(kwargs["length"]))
                .offset(int(kwargs["start"]))
                .all()
            ],
        }

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

    def switch_menu(self, user_id):
        user = fetch("user", id=user_id)
        user.small_menu = not user.small_menu

    def update_database_configurations_from_git(self):
        for dir in scandir(self.path / "network_data"):
            device = fetch("device", allow_none=True, name=dir.name)
            if not device:
                continue
            with open(Path(dir.path) / "data.yml") as data:
                parameters = yaml.load(data)
                device.update(**{"dont_update_pools": True, **parameters})
            for data in ("configuration", "operational_data"):
                filepath = Path(dir.path) / data
                if not filepath.exists():
                    continue
                with open(filepath) as file:
                    setattr(device, data, file.read())
        Session.commit()
        for pool in fetch_all("pool"):
            if pool.device_configuration or pool.device_operational_data:
                pool.compute_pool()

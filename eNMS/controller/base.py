from apscheduler.schedulers.background import BackgroundScheduler
from collections import Counter
from datetime import datetime
from flask import Flask
from hvac import Client as VaultClient
from importlib import import_module
from importlib.abc import Loader
from importlib.util import spec_from_file_location, module_from_spec
from json.decoder import JSONDecodeError
from ldap3 import ALL, Server
from logging import basicConfig, error, info, StreamHandler, warning
from logging.handlers import RotatingFileHandler
from os import environ
from pathlib import Path
from string import punctuation
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from tacacs_plus.client import TACACSClient
from typing import Any, List, Set

from eNMS.database import Session
from eNMS.database.functions import count, delete, factory, fetch, fetch_all
from eNMS.models import models, model_properties
from eNMS.properties.diagram import diagram_classes, type_to_diagram_properties
from eNMS.syslog import SyslogServer


class BaseController:

    parameters = [
        ("cluster", False),
        ("cluster_id", True),
        ("cluster_scan_subnet", "192.168.105.0/24"),
        ("cluster_scan_protocol", "http"),
        ("cluster_scan_timeout", 0.05),
        ("default_longitude", -96.0),
        ("default_latitude", 33.0),
        ("default_zoom_level", 5),
        ("default_view", "2D"),
        ("default_marker", "Image"),
        ("create_examples", True),
        ("custom_services_path", ""),
        ("enms_config_mode", ""),
        ("enms_log_level", "DEBUG"),
        ("enms_server_addr", ""),
        ("git_automation", ""),
        ("git_configurations", ""),
        ("gotty_port_redirection", False),
        ("gotty_bypass_key_prompt", ""),
        ("gotty_port", -1),
        ("gotty_start_port", 9000),
        ("gotty_end_port", 9100),
        ("ldap_server", ""),
        ("ldap_userdn", ""),
        ("ldap_basedn", ""),
        ("ldap_admin_group", ""),
        ("mattermost_url", ""),
        ("mattermost_channel", ""),
        ("mattermost_verify_certificate", True),
        ("pool_filter", "All objects"),
        ("slack_token", ""),
        ("slack_channel", ""),
        ("syslog_addr", "0.0.0.0"),
        ("syslog_port", 514),
        ("tacacs_addr", ""),
        ("tacacs_password", ""),
        ("unseal_vault", ""),
        ("use_ldap", False),
        ("use_syslog", False),
        ("use_tacacs", False),
        ("use_vault", False),
        ("vault_addr", ""),
    ]

    valid_post_endpoints = [
        "add_edge",
        "add_jobs_to_workflow",
        "calendar_init",
        "clear_results",
        "clear_configurations",
        "connection",
        "counters",
        "count_models",
        "database_deletion",
        "delete_edge",
        "delete_instance",
        "delete_node",
        "duplicate_workflow",
        "export_to_google_earth",
        "export_topology",
        "get",
        "get_all",
        "get_cluster_status",
        "get_configurations",
        "get_configuration_diff",
        "get_device_logs",
        "get_git_content",
        "get_job_logs",
        "get_job_results",
        "get_results_diff",
        "get_view_topology",
        "import_topology",
        "migration_export",
        "migration_import",
        "query_netbox",
        "query_librenms",
        "query_opennms",
        "reset_status",
        "run_job",
        "save_device_jobs",
        "save_parameters",
        "save_pool_objects",
        "save_positions",
        "scan_cluster",
        "scheduler",
        "task_action",
        "topology_import",
        "update",
        "update_parameters",
        "update_pools",
        "view_filtering",
    ]

    log_severity = {"error": error, "info": info, "warning": warning}

    @property
    def config(self):
        return {parameter: getattr(self, parameter) for parameter, _ in self.parameters}

    def __init__(self) -> None:
        self.init_variables()
        self.custom_properties = self.load_custom_properties()
        self.init_scheduler()
        if self.use_tacacs:
            self.init_tacacs_client()
        if self.use_ldap:
            self.init_ldap_client()
        if self.use_vault:
            self.init_vault_client()
        if self.use_syslog:
            self.init_syslog_server()

    def init_app(self, app: Flask) -> None:
        self.app = app
        self.path = app.path
        self.create_google_earth_styles()
        self.init_logs()

    def init_database(self):
        self.init_parameters()
        self.create_default()
        if self.create_examples:
            self.examples_creation()

    def init_parameters(self) -> None:
        parameters = Session.query(models["Parameters"]).one_or_none()
        if not parameters:
            parameters = models["Parameters"]()
            parameters.update(
                **{
                    property: self.config[property]
                    for property in model_properties["Parameters"]
                    if property in self.config
                }
            )
            Session.add(parameters)
            Session.commit()
        else:
            for parameter, _ in self.parameters:
                if hasattr(parameters, parameter):
                    setattr(self, parameter, getattr(parameters, parameter))

    def init_logs(self) -> None:
        basicConfig(
            level=getattr(import_module("logging"), self.enms_log_level),
            format="%(asctime)s %(levelname)-8s %(message)s",
            datefmt="%m-%d-%Y %H:%M:%S",
            handlers=[
                RotatingFileHandler(
                    self.path / "logs" / "app_logs" / "enms.log",
                    maxBytes=20_000_000,
                    backupCount=10,
                ),
                StreamHandler(),
            ],
        )

    def init_scheduler(self) -> None:
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

    def init_variables(self) -> None:
        for parameter, default in self.parameters:
            value = environ.get(parameter.upper()) or default
            func = int if isinstance(default, bool) else type(default)
            setattr(self, parameter, func(value))

    def init_services(self) -> None:
        path_services = [self.path / "eNMS" / "services"]
        if self.custom_services_path:
            path_services.append(Path(self.custom_services_path))
        for path in path_services:
            for file in path.glob("**/*.py"):
                if "init" in str(file):
                    continue
                if not self.create_examples and "examples" in str(file):
                    continue
                spec = spec_from_file_location(str(file).split("/")[-1][:-3], str(file))
                assert isinstance(spec.loader, Loader)
                module = module_from_spec(spec)
                try:
                    spec.loader.exec_module(module)
                except InvalidRequestError as e:
                    error(f"Error loading custom service '{file}' ({str(e)})")

    def init_ldap_client(self) -> None:
        self.ldap_client = Server(self.ldap_server, get_info=ALL)

    def init_tacacs_client(self) -> None:
        self.tacacs_client = TACACSClient(self.tacacs_addr, 49, self.tacacs_password)

    def init_vault_client(self) -> None:
        self.vault_client = VaultClient()
        self.vault_client.url = self.vault_addr
        self.vault_client.token = environ.get("VAULT_TOKEN")
        if self.vault_client.sys.is_sealed() and self.unseal_vault:
            keys = [environ.get(f"UNSEAL_VAULT_KEY{i}") for i in range(1, 6)]
            self.vault_client.sys.submit_unseal_keys(filter(None, keys))

    def init_syslog_server(self) -> None:
        self.syslog_server = SyslogServer(self.syslog_addr, self.syslog_port)
        self.syslog_server.start()

    def update_parameters(self, **kwargs):
        Session.query(models["Parameters"]).one().update(**kwargs)
        self.config.update(kwargs)

    def delete_instance(self, cls: str, instance_id: int) -> dict:
        return delete(cls, id=instance_id)

    def get(self, cls: str, id: str) -> dict:
        return fetch(cls, id=id).serialized

    def get_all(self, cls: str) -> List[dict]:
        return [instance.get_properties() for instance in fetch_all(cls)]

    def update(self, cls: str, **kwargs) -> dict:
        try:
            instance = factory(cls, **kwargs)
            return instance.serialized
        except JSONDecodeError:
            return {"error": "Invalid JSON syntax (JSON field)"}
        except IntegrityError:
            return {"error": "An object with the same name already exists"}

    def log(self, severity, content) -> None:
        factory("Log", **{"origin": "eNMS", "severity": severity, "content": content})
        self.log_severity[severity](content)

    def count_models(self):
        return {
            "counters": {
                **{cls: count(cls) for cls in diagram_classes},
                **{
                    "active-Service": count("Service", status="Running"),
                    "active-Workflow": count("Workflow", status="Running"),
                    "active-Task": count("Task", status="Active"),
                },
            },
            "properties": {
                cls: Counter(
                    str(getattr(instance, type_to_diagram_properties[cls][0]))
                    for instance in fetch_all(cls)
                )
                for cls in diagram_classes
            },
        }

    def allowed_file(self, name: str, allowed_modules: Set[str]) -> bool:
        allowed_syntax = "." in name
        allowed_extension = name.rsplit(".", 1)[1].lower() in allowed_modules
        return allowed_syntax and allowed_extension

    def get_time(self) -> str:
        return str(datetime.now())

    def str_dict(self, input: Any, depth: int = 0) -> str:
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

    def strip_all(self, input: str) -> str:
        return input.translate(str.maketrans("", "", f"{punctuation} "))

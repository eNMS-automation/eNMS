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
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from string import punctuation
from tacacs_plus.client import TACACSClient
from typing import Any, List, Set

from eNMS.database import Session
from eNMS.database.functions import count, delete, factory, fetch, fetch_all
from eNMS.models import models, model_properties
from eNMS.properties.diagram import diagram_classes, type_to_diagram_properties
from eNMS.syslog import SyslogServer


class BaseController:
    def load_config(self) -> dict:
        return {
            "cluster": int(environ.get("CLUSTER", False)),
            "cluster_id": int(environ.get("CLUSTER_ID", True)),
            "cluster_scan_subnet": environ.get(
                "CLUSTER_SCAN_SUBNET", "192.168.105.0/24"
            ),
            "cluster_scan_protocol": environ.get("CLUSTER_SCAN_PROTOCOL", "http"),
            "cluster_scan_timeout": float(environ.get("CLUSTER_SCAN_TIMEOUT", 0.05)),
            "default_longitude": float(environ.get("DEFAULT_LONGITUDE", -96.0)),
            "default_latitude": float(environ.get("DEFAULT_LATITUDE", 33.0)),
            "default_zoom_level": int(environ.get("DEFAULT_ZOOM_LEVEL", 5)),
            "default_view": environ.get("DEFAULT_VIEW", "2D"),
            "default_marker": environ.get("DEFAULT_MARKER", "Image"),
            "create_examples": int(environ.get("CREATE_EXAMPLES", True)),
            "custom_services_path": environ.get("CUSTOM_SERVICES_PATH"),
            "enms_config_mode": environ.get("ENMS_CONFIG_MODE"),
            "enms_log_level": environ.get("ENMS_LOG_LEVEL", "DEBUG").upper(),
            "enms_server_addr": environ.get("ENMS_SERVER_ADDR"),
            "git_automation": environ.get("GIT_AUTOMATION", ""),
            "git_configurations": environ.get("GIT_CONFIGURATIONS", ""),
            "gotty_port_redirection": int(environ.get("GOTTY_PORT_REDIRECTION", False)),
            "gotty_bypass_key_prompt": environ.get("GOTTY_BYPASS_KEY_PROMPT"),
            "gotty_port": -1,
            "gotty_start_port": int(environ.get("GOTTY_START_PORT", 9000)),
            "gotty_end_port": int(environ.get("GOTTY_END_PORT", 9100)),
            "ldap_server": environ.get("LDAP_SERVER"),
            "ldap_userdn": environ.get("LDAP_USERDN"),
            "ldap_basedn": environ.get("LDAP_BASEDN"),
            "ldap_admin_group": environ.get("LDAP_ADMIN_GROUP", "").split(","),
            "mattermost_url": environ.get("MATTERMOST_URL", ""),
            "mattermost_channel": environ.get("MATTERMOST_CHANNEL", ""),
            "mattermost_verify_certificate": int(
                environ.get("MATTERMOST_VERIFY_CERTIFICATE", True)
            ),
            "pool_filter": environ.get("POOL_FILTER", "All objects"),
            "slack_token": environ.get("SLACK_TOKEN", ""),
            "slack_channel": environ.get("SLACK_CHANNEL", ""),
            "syslog_addr": environ.get("SYSLOG_ADDR", "0.0.0.0"),
            "syslog_port": int(environ.get("SYSLOG_PORT", 514)),
            "tacacs_addr": environ.get("TACACS_ADDR"),
            "tacacs_password": environ.get("TACACS_PASSWORD"),
            "unseal_vault": environ.get("UNSEAL_VAULT"),
            "use_ldap": int(environ.get("USE_LDAP", False)),
            "use_syslog": int(environ.get("USE_SYSLOG", False)),
            "use_tacacs": int(environ.get("USE_TACACS", False)),
            "use_vault": int(environ.get("USE_VAULT", False)),
            "vault_addr": environ.get("VAULT_ADDR"),
        }

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

    def configure_scheduler(self) -> None:
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

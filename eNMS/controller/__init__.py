from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from flask import Flask
from hvac import Client as VaultClient
from importlib import import_module
from importlib.abc import Loader
from importlib.util import spec_from_file_location, module_from_spec
from ldap3 import ALL, Server
from logging import basicConfig, error, info, StreamHandler, warning
from logging.handlers import RotatingFileHandler
from os import environ
from pathlib import Path
from sqlalchemy.exc import InvalidRequestError
from string import punctuation
from tacacs_plus.client import TACACSClient
from typing import Any, Set

from eNMS.controller.automation import AutomationController
from eNMS.controller.inventory import InventoryController
from eNMS.database.functions import factory, get_one


class Controller(AutomationController, InventoryController):

    cache = [
        "administration",
        "calendar",
        "dashboard",
        "form",
        "view",
        "table",
        "workflow_builder",
    ]

    log_severity = {"error": error, "info": info, "warning": warning}

    def __init__(self) -> None:
        self.USE_SYSLOG = int(environ.get("USE_SYSLOG", False))
        self.USE_TACACS = int(environ.get("USE_TACACS", False))
        self.USE_LDAP = int(environ.get("USE_LDAP", False))
        self.USE_VAULT = int(environ.get("USE_VAULT", False))
        self.config = self.load_config()
        self.custom_properties = self.load_custom_properties()
        self.configure_scheduler()
        if self.USE_TACACS:
            self.configure_tacacs_client()
        if self.USE_LDAP:
            self.configure_ldap_client()
        if self.USE_VAULT:
            self.configure_vault_client()

    def init_app(self, app: Flask) -> None:
        self.app = app
        self.config.update(app.config)
        self.path = app.path
        self.create_google_earth_styles()
        self.configure_logs()

    @property
    def parameters(self):
        return get_one("Parameters")

    def unless_cache(self, *args, **kwargs):
        page = kwargs["page"].split("-")[0]
        return self.config["DEVELOP"] or page not in self.cache

    def configure_logs(self) -> None:
        basicConfig(
            level=getattr(
                import_module("logging"), controller.config["ENMS_LOG_LEVEL"]
            ),
            format="%(asctime)s %(levelname)-8s %(message)s",
            datefmt="%m-%d-%Y %H:%M:%S",
            handlers=[
                RotatingFileHandler(
                    self.app.path / "logs" / "app_logs" / "enms.log",
                    maxBytes=20_000_000,
                    backupCount=10,
                ),
                StreamHandler(),
            ],
        )

    def log(self, severity, content) -> None:
        factory(
            "Log",
            commit=False,
            **{"origin": "eNMS", "severity": severity, "content": content},
        )
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

    def load_services(self) -> None:
        path_services = [self.app.path / "eNMS" / "services"]
        custom_services_path = self.config["CUSTOM_SERVICES_PATH"]
        if custom_services_path:
            path_services.append(Path(custom_services_path))
        for path in path_services:
            for file in path.glob("**/*.py"):
                if "init" in str(file):
                    continue
                if not self.config["CREATE_EXAMPLES"] and "examples" in str(file):
                    continue
                spec = spec_from_file_location(str(file).split("/")[-1][:-3], str(file))
                assert isinstance(spec.loader, Loader)
                module = module_from_spec(spec)
                try:
                    spec.loader.exec_module(module)
                except InvalidRequestError as e:
                    error(f"Error loading custom service '{file}' ({str(e)})")

    def configure_ldap_client(self) -> None:
        self.LDAP_SERVER = environ.get("LDAP_SERVER")
        self.LDAP_USERDN = environ.get("LDAP_USERDN")
        self.LDAP_BASEDN = environ.get("LDAP_BASEDN")
        self.LDAP_ADMIN_GROUP = environ.get("LDAP_ADMIN_GROUP", "").split(",")
        self.ldap_client = Server(environ.get("LDAP_SERVER"), get_info=ALL)

    def configure_tacacs_client(self) -> None:
        self.tacacs_client = TACACSClient(
            environ.get("TACACS_ADDR"), 49, environ.get("TACACS_PASSWORD")
        )

    def configure_vault_client(self) -> None:
        self.vault_client = VaultClient()
        self.vault_client.url = environ.get("VAULT_ADDR")
        self.vault_client.token = environ.get("VAULT_TOKEN")
        if self.vault_client.sys.is_sealed() and environ.get("UNSEAL_VAULT"):
            keys = [environ.get(f"UNSEAL_VAULT_KEY{i}") for i in range(1, 6)]
            self.vault_client.sys.submit_unseal_keys(filter(None, keys))

    def allowed_file(self, name: str, allowed_modules: Set[str]) -> bool:
        allowed_syntax = "." in name
        allowed_extension = name.rsplit(".", 1)[1].lower() in allowed_modules
        return allowed_syntax and allowed_extension

    def get_time(self) -> str:
        return str(datetime.now()).replace("-", "+")

    def load_config(self) -> dict:
        return {
            "CLUSTER": int(environ.get("CLUSTER", False)),
            "CLUSTER_ID": int(environ.get("CLUSTER_ID", True)),
            "CLUSTER_SCAN_SUBNET": environ.get(
                "CLUSTER_SCAN_SUBNET", "192.168.105.0/24"
            ),
            "CLUSTER_SCAN_PROTOCOL": environ.get("CLUSTER_SCAN_PROTOCOL", "http"),
            "CLUSTER_SCAN_TIMEOUT": float(environ.get("CLUSTER_SCAN_TIMEOUT", 0.05)),
            "DEFAULT_LONGITUDE": float(environ.get("DEFAULT_LONGITUDE", -96.0)),
            "DEFAULT_LATITUDE": float(environ.get("DEFAULT_LATITUDE", 33.0)),
            "DEFAULT_ZOOM_LEVEL": int(environ.get("DEFAULT_ZOOM_LEVEL", 5)),
            "DEFAULT_VIEW": environ.get("DEFAULT_VIEW", "2D"),
            "DEFAULT_MARKER": environ.get("DEFAULT_MARKER", "Image"),
            "CREATE_EXAMPLES": int(environ.get("CREATE_EXAMPLES", True)),
            "CUSTOM_SERVICES_PATH": environ.get("CUSTOM_SERVICES_PATH"),
            "ENMS_LOG_LEVEL": environ.get("ENMS_LOG_LEVEL", "DEBUG").upper(),
            "ENMS_SERVER_ADDR": environ.get("ENMS_SERVER_ADDR"),
            "GIT_AUTOMATION": environ.get("GIT_AUTOMATION", ""),
            "GIT_CONFIGURATIONS": environ.get("GIT_CONFIGURATIONS", ""),
            "GOTTY_PORT_REDIRECTION": int(environ.get("GOTTY_PORT_REDIRECTION", False)),
            "GOTTY_BYPASS_KEY_PROMPT": environ.get("GOTTY_BYPASS_KEY_PROMPT"),
            "GOTTY_START_PORT": int(environ.get("GOTTY_START_PORT", 9000)),
            "GOTTY_END_PORT": int(environ.get("GOTTY_END_PORT", 9100)),
            "MATTERMOST_URL": environ.get("MATTERMOST_URL", ""),
            "MATTERMOST_CHANNEL": environ.get("MATTERMOST_CHANNEL", ""),
            "MATTERMOST_VERIFY_CERTIFICATE": int(
                environ.get("MATTERMOST_VERIFY_CERTIFICATE", True)
            ),
            "POOL_FILTER": environ.get("POOL_FILTER", "All objects"),
            "SLACK_TOKEN": environ.get("SLACK_TOKEN", ""),
            "SLACK_CHANNEL": environ.get("SLACK_CHANNEL", ""),
        }

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


controller = Controller()

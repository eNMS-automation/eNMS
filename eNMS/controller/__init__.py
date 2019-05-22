from apscheduler.schedulers.background import BackgroundScheduler
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
from tacacs_plus.client import TACACSClient
from typing import Any

from eNMS.controller.administration import AdministrationController
from eNMS.controller.automation import AutomationController
from eNMS.controller.default import DefaultController
from eNMS.controller.examples import ExamplesController
from eNMS.controller.inventory import InventoryController
from eNMS.database import Session
from eNMS.models import models, model_properties
from eNMS.syslog import SyslogServer


class Controller(
    AdministrationController,
    AutomationController,
    DefaultController,
    ExamplesController,
    InventoryController,
):

    parameters = [
        "cluster",
        "cluster_id",
        "cluster_scan_subnet",
        "cluster_scan_protocol",
        "cluster_scan_timeout",
        "default_longitude",
        "default_latitude",
        "default_zoom_level",
        "default_view",
        "default_marker",
        "create_examples",
        "custom_services_path",
        "enms_config_mode",
        "enms_log_level",
        "enms_server_addr",
        "git_automation",
        "git_configurations",
        "gotty_port_redirection",
        "gotty_bypass_key_prompt",
        "gotty_port",
        "gotty_start_port",
        "gotty_end_port",
        "ldap_server",
        "ldap_userdn",
        "ldap_basedn",
        "ldap_admin_group",
        "mattermost_url",
        "mattermost_channel",
        "mattermost_verify_certificate",
        "pool_filter",
        "slack_token",
        "slack_channel",
        "syslog_addr",
        "syslog_port",
        "tacacs_addr",
        "tacacs_password",
        "unseal_vault",
        "use_ldap",
        "use_syslog",
        "use_tacacs",
        "use_vault",
        "vault_addr",
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
        "database_helpers",
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

    def __init__(self) -> None:
        self.init_variables()
        self.custom_properties = self.load_custom_properties()
        self.init_scheduler()
        if self.use_tacacs:
            self.configure_tacacs_client()
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
            for parameter in self.parameters:
                if hasattr(parameters, parameter):
                    setattr(self, parameter, getattr(parameters, parameter))

    def init_logs(self) -> None:
        basicConfig(
            level=getattr(import_module("logging"), self.enms_log_level),
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
        self.cluster = int(environ.get("CLUSTER", False))
        self.cluster_id = int(environ.get("CLUSTER_ID", True))
        self.cluster_scan_subnet = environ.get(
            "CLUSTER_SCAN_SUBNET", "192.168.105.0/24"
        )
        self.cluster_scan_protocol = environ.get("CLUSTER_SCAN_PROTOCOL", "http")
        self.cluster_scan_timeout = float(environ.get("CLUSTER_SCAN_TIMEOUT", 0.05))
        self.default_longitude = float(environ.get("DEFAULT_LONGITUDE", -96.0))
        self.default_latitude = float(environ.get("DEFAULT_LATITUDE", 33.0))
        self.default_zoom_level = int(environ.get("DEFAULT_ZOOM_LEVEL", 5))
        self.default_view = environ.get("DEFAULT_VIEW", "2D")
        self.default_marker = environ.get("DEFAULT_MARKER", "Image")
        self.create_examples = int(environ.get("CREATE_EXAMPLES", True))
        self.custom_services_path = environ.get("CUSTOM_SERVICES_PATH")
        self.enms_config_mode = environ.get("ENMS_CONFIG_MODE")
        self.enms_log_level = environ.get("ENMS_LOG_LEVEL", "DEBUG").upper()
        self.enms_server_addr = environ.get("ENMS_SERVER_ADDR")
        self.git_automation = environ.get("GIT_AUTOMATION", "")
        self.git_configurations = environ.get("GIT_CONFIGURATIONS", "")
        self.gotty_port_redirection = int(environ.get("GOTTY_PORT_REDIRECTION", False))
        self.gotty_bypass_key_prompt = environ.get("GOTTY_BYPASS_KEY_PROMPT")
        self.gotty_port = -1
        self.gotty_start_port = int(environ.get("GOTTY_START_PORT", 9000))
        self.gotty_end_port = int(environ.get("GOTTY_END_PORT", 9100))
        self.ldap_server = environ.get("LDAP_SERVER")
        self.ldap_userdn = environ.get("LDAP_USERDN")
        self.ldap_basedn = environ.get("LDAP_BASEDN")
        self.ldap_admin_group = environ.get("LDAP_ADMIN_GROUP", "").split(",")
        self.mattermost_url = environ.get("MATTERMOST_URL", "")
        self.mattermost_channel = environ.get("MATTERMOST_CHANNEL", "")
        self.mattermost_verify_certificate = int(
            environ.get("MATTERMOST_VERIFY_CERTIFICATE", True)
        )
        self.pool_filter = environ.get("POOL_FILTER", "All objects")
        self.slack_token = environ.get("SLACK_TOKEN", "")
        self.slack_channel = environ.get("SLACK_CHANNEL", "")
        self.syslog_addr = environ.get("SYSLOG_ADDR", "0.0.0.0")
        self.syslog_port = int(environ.get("SYSLOG_PORT", 514))
        self.tacacs_addr = environ.get("TACACS_ADDR")
        self.tacacs_password = environ.get("TACACS_PASSWORD")
        self.unseal_vault = environ.get("UNSEAL_VAULT")
        self.use_ldap = int(environ.get("USE_LDAP", False))
        self.use_syslog = int(environ.get("USE_SYSLOG", False))
        self.use_tacacs = int(environ.get("USE_TACACS", False))
        self.use_vault = int(environ.get("USE_VAULT", False))
        self.vault_addr = environ.get("VAULT_ADDR")

    def init_services(self) -> None:
        path_services = [self.app.path / "eNMS" / "services"]
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

    def configure_tacacs_client(self) -> None:
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


controller = Controller()

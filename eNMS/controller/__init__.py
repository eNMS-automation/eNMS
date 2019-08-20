from flask import Flask
from json import load
from pathlib import Path
from simplekml import Color, Style
from sqlalchemy.orm import configure_mappers
from sys import path as sys_path
from typing import Dict
from uuid import getnode

from eNMS.controller.administration import AdministrationController
from eNMS.controller.automation import AutomationController
from eNMS.controller.inventory import InventoryController
from eNMS.database import Base, engine, Session
from eNMS.database.functions import factory, fetch
from eNMS.framework import create_app
from eNMS.models import models, model_properties
from eNMS.properties.database import import_classes
from eNMS.properties.objects import device_icons


class Controller(AdministrationController, AutomationController, InventoryController):

    free_access_pages = ["/", "/login"]

    valid_pages = [
        "/administration",
        "/calendar/run",
        "/calendar/task",
        "/dashboard",
        "/login",
        "/table/changelog",
        "/table/configuration",
        "/table/device",
        "/table/event",
        "/table/pool",
        "/table/link",
        "/table/run",
        "/table/server",
        "/table/service",
        "/table/syslog",
        "/table/task",
        "/table/user",
        "/table/workflow",
        "/view/network",
        "/view/site",
        "/workflow_builder",
    ]

    valid_post_endpoints = [
        "add_edge",
        "add_jobs_to_workflow",
        "calendar_init",
        "clear_results",
        "clear_configurations",
        "compare_results",
        "connection",
        "counters",
        "count_models",
        "database_deletion",
        "delete_edge",
        "delete_instance",
        "delete_node",
        "duplicate_workflow",
        "export_job",
        "export_to_google_earth",
        "export_topology",
        "filtering",
        "get",
        "get_all",
        "get_cluster_status",
        "get_configurations",
        "get_configuration_diff",
        "get_device_list",
        "get_device_logs",
        "get_exported_jobs",
        "get_git_content",
        "get_job_list",
        "get_job_logs",
        "get_properties",
        "get_results",
        "get_results_diff",
        "get_runtimes",
        "get_view_topology",
        "get_workflow_device_list",
        "get_workflow_state",
        "import_jobs",
        "import_topology",
        "migration_export",
        "migration_import",
        "query_netbox",
        "query_librenms",
        "query_opennms",
        "reset_status",
        "restart_workflow",
        "run_job",
        "save_parameters",
        "save_pool_objects",
        "save_positions",
        "scan_cluster",
        "scan_playbook_folder",
        "scheduler",
        "task_action",
        "topology_import",
        "update",
        "update_parameters",
        "update_pool",
        "update_all_pools",
        "view_filtering",
    ]

    valid_rest_endpoints = [
        "get_cluster_status",
        "get_git_content",
        "update_all_pools",
        "update_database_configurations_from_git",
    ]

    def __init__(self) -> None:
        self.custom_properties = self.load_custom_properties()
        self.custom_config = self.load_custom_config()
        self.init_scheduler()
        if self.use_tacacs:
            self.init_tacacs_client()
        if self.use_ldap:
            self.init_ldap_client()
        if self.use_vault:
            self.init_vault_client()
        if self.use_syslog:
            self.init_syslog_server()
        if self.custom_code_path:
            sys_path.append(self.custom_code_path)

    def create_google_earth_styles(self) -> None:
        self.google_earth_styles: Dict[str, Style] = {}
        for icon in device_icons:
            point_style = Style()
            point_style.labelstyle.color = Color.blue
            path_icon = f"{self.path}/eNMS/static/images/2D/{icon}.gif"
            point_style.iconstyle.icon.href = path_icon
            self.google_earth_styles[icon] = point_style

    def fetch_version(self) -> None:
        with open(self.path / "package.json") as package_file:
            self.version = load(package_file)["version"]

    def configure_database(self, app: Flask) -> None:
        Base.metadata.create_all(bind=engine)
        from eNMS.database.events import configure_events
        configure_events(self)
        configure_mappers()

        @app.before_first_request
        def initialize_database() -> None:
            self.clean_database()
            if not fetch("User", allow_none=True, name="admin"):
                self.init_database()

    def init_parameters(self) -> None:
        parameters = Session.query(models["Parameters"]).one_or_none()
        if not parameters:
            parameters = models["Parameters"]()
            parameters.update(
                **{
                    property: getattr(self, property)
                    for property in model_properties["Parameters"]
                    if hasattr(self, property)
                }
            )
            Session.add(parameters)
            Session.commit()
        else:
            for parameter in parameters.get_properties():
                setattr(self, parameter, getattr(parameters, parameter))

    def configure_server_id(self) -> None:
        factory(
            "Server",
            **{
                "name": str(getnode()),
                "description": "Localhost",
                "ip_address": "0.0.0.0",
                "status": "Up",
            },
        )

    def create_admin_user(self) -> None:
        factory("User", **{"name": "admin", "password": "admin"})

    def update_credentials(self) -> None:
        with open(self.path / "projects" / "spreadsheets" / "usa.xls", "rb") as file:
            self.topology_import(file)

    def clean_database(self) -> None:
        for run in fetch("Run", all_matches=True, allow_none=True, status="Running"):
            run.status = "Aborted (app reload)"
        Session.commit()

    def init_database(self) -> None:
        self.init_parameters()
        self.configure_server_id()
        self.create_admin_user()
        Session.commit()
        if self.create_examples:
            self.migration_import(name="examples", import_export_types=import_classes)
            self.update_credentials()
        else:
            self.migration_import(name="default", import_export_types=import_classes)
        self.get_git_content()
        Session.commit()

    def init_app(self, path: Path) -> None:
        self.path = path
        self.init_services()
        app = create_app(self)
        self.configure_database(app)
        self.init_forms()
        self.create_google_earth_styles()
        self.fetch_version()
        self.init_logs()
        return app

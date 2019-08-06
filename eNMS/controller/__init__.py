from typing import Any
from uuid import getnode

from eNMS.controller.administration import AdministrationController
from eNMS.controller.automation import AutomationController
from eNMS.controller.inventory import InventoryController
from eNMS.database import Session
from eNMS.database.functions import factory, fetch
from eNMS.models import models, model_properties
from eNMS.properties.database import import_classes


class Controller(AdministrationController, AutomationController, InventoryController):
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

    def eval(_self, query: str, _run: Any, **locals: Any) -> Any:  # noqa: N805
        try:
            return eval(
                query,
                {
                    "get_var": _self.get_var(locals["payload"]),
                    "get_result": _self.get_result(_run.parent_runtime),
                    "config": _self.custom_config,
                    "workflow_device": _run.workflow_device,
                    **locals,
                },
            )
        except Exception as exc:
            raise Exception(
                "Python Query / Variable Substitution Failure."
                " Check that all variables are defined."
                " If you are using the 'device' variable, "
                f"check that the service has targets. ({str(exc)})"
            )

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


controller = Controller()

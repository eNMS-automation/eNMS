from uuid import getnode

from eNMS.controller.administration import AdministrationController
from eNMS.controller.automation import AutomationController
from eNMS.controller.inventory import InventoryController
from eNMS.database import Session
from eNMS.database.functions import factory
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

    def init_database(self) -> None:
        self.init_parameters()
        self.configure_server_id()
        self.migration_import(
            name="examples" if self.create_examples else "default",
            import_export_types=import_classes,
        )
        self.get_git_content()


controller = Controller()

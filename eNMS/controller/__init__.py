from eNMS.controller.administration_controller import AdministrationController
from eNMS.controller.automation_controller import AutomationController
from eNMS.controller.base_controller import BaseController
from eNMS.controller.import_export_controller import ImportExportController
from eNMS.controller.inventory_controller import InventoryController


class Controller(
    AutomationController,
    AdministrationController,
    BaseController,
    ImportExportController,
    InventoryController,
):
    def init_app(self, app: Flask, session: Session):
        self.app = app
        self.session = session


controller = Controller()

from eNMS.controller.administration import AdministrationController
from eNMS.controller.automation import AutomationController
from eNMS.controller.default import DefaultController
from eNMS.controller.examples import ExamplesController
from eNMS.controller.inventory import InventoryController


class Controller(
    AdministrationController,
    AutomationController,
    DefaultController,
    ExamplesController,
    InventoryController,
):
    pass


controller = Controller()

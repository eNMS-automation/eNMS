from eNMS.controller.administration import AdministrationController
from eNMS.controller.automation import AutomationController
from eNMS.controller.inventory import InventoryController
from eNMS.plugins.controller import CustomController


class App(
    AdministrationController,
    AutomationController,
    CustomController,
    InventoryController,
):
    pass

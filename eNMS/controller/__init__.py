from eNMS.config import config
from eNMS.controller.administration import AdministrationController
from eNMS.controller.automation import AutomationController
from eNMS.controller.inventory import InventoryController


class App(AdministrationController, AutomationController, InventoryController):
    pass
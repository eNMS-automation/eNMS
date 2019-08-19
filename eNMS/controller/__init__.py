from uuid import getnode

from eNMS.controller.administration import AdministrationController
from eNMS.controller.automation import AutomationController
from eNMS.controller.inventory import InventoryController


class Controller(AdministrationController, AutomationController, InventoryController):
    pass

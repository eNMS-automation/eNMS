from functools import wraps

from eNMS import app
from eNMS.controller.administration import BaseController
from eNMS.controller.automation import AutomationController
from eNMS.database import db


class Controller(BaseController, AutomationController):
    def register_endpoint(self, func):
        setattr(self, func.__name__, func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper


controller = Controller()

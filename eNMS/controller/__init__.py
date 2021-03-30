from functools import wraps

from eNMS import app
from eNMS.controller.administration import BaseController
from eNMS.controller.automation import AutomationController
from eNMS.controller.inventory import InventoryController
from eNMS.database import db
from eNMS.models import models


class Controller(BaseController, AutomationController, InventoryController):
    def initialize(self):
        self.configure_database()
        self.configure_server_id()
        self.reset_run_status()

    def configure_database(self):
        if db.get_user("admin"):
            return
        admin_user = models["user"](name="admin", is_admin=True)
        db.session.add(admin_user)
        db.session.commit()
        if not admin_user.password:
            admin_user.update(password="admin")
        self.migration_import(
            name=app.settings["app"].get("startup_migration", "default"),
            import_export_types=db.import_export_models,
        )
        self.get_git_content()

    def configure_server_id(self):
        db.factory(
            "server",
            **{
                "name": str(getnode()),
                "description": "Localhost",
                "ip_address": "0.0.0.0",
                "status": "Up",
            },
        )

    def reset_run_status(self):
        for run in db.fetch("run", all_matches=True, allow_none=True, status="Running"):
            run.status = "Aborted (RELOAD)"
            run.service.status = "Idle"
        db.session.commit()

    def register_endpoint(self, func):
        setattr(self, func.__name__, func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper


controller = Controller()

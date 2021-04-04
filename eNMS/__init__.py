from uuid import getnode

from eNMS.app import app
from eNMS.controller import controller
from eNMS.database import db
from eNMS.forms import form_factory
from eNMS.models import models
from eNMS.variables import vs


class Initialization:
    def __init__(self):
        app.initialize()
        form_factory.initialize()
        if app.cli_command:
            return
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
        controller.migration_import(
            name=vs.settings["app"].get("startup_migration", "default"),
            import_export_types=db.import_export_models,
        )
        controller.get_git_content()

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


Initialization()

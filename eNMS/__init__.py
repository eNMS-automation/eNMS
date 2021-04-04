from eNMS.app import app
from eNMS.controller import controller
from eNMS.database import db
from eNMS.forms import form_factory


def initialize():
    app.initialize()
    form_factory.initialize()
    if app.cli_command:
        return
    first_init = db.initialize()
    controller._initialize(first_init)


initialize()

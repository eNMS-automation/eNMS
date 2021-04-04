from eNMS.app import app
from eNMS.controller import controller
from eNMS.database import db
from eNMS.forms import form_factory
from eNMS.variables import vs


def initialize():
    app._initialize()
    form_factory._initialize()
    if app.cli_command:
        return
    first_init = db._initialize()
    controller._initialize(first_init)


initialize()

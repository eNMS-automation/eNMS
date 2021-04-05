from eNMS.app import app
from eNMS.controller import controller
from eNMS.database import db
from eNMS.forms import form_factory
from eNMS.variables import vs


def initialize():
    app._initialize()
    form_factory._initialize()
    if app.detect_cli():
        return
    first_init = db._initialize(app)
    controller._initialize(first_init)
    vs._initialize()


initialize()

from eNMS.app import app
from eNMS.controller import controller
from eNMS.database import db
from eNMS.forms import form_factory
from eNMS.variables import vs


def initialize():
    app._initialize()
    first_init = db._initialize(app)
    if app.detect_cli():
        return
    form_factory._initialize()
    controller._initialize(first_init)
    vs._initialize()


initialize()

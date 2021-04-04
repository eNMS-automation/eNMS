from eNMS.app import app
from eNMS.controller import controller
from eNMS.database import db
from eNMS.forms import form_factory


def initialize():
    app._initialize()
    form_factory._initialize()
    if app.detect_cli():
        return
    first_init = db._initialize()
    controller._initialize(first_init)


initialize()

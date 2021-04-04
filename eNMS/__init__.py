from eNMS.app import app
from eNMS.controller import controller
from eNMS.database import db
from eNMS.forms import form_factory


class Initialization:
    def __init__(self):
        app.initialize()
        form_factory.initialize()
        if app.cli_command:
            return
        if db.initialize():
            controller._initialize()


Initialization()

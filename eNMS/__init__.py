from eNMS.app import app
from eNMS.controller import controller
from eNMS.database import db
from eNMS.forms import form_factory
from eNMS.models import models


class Initialization:
    def __init__(self):
        app.initialize()
        form_factory.initialize()
        if app.cli_command:
            return
        if db.initialize():
            controller._initialize()

Initialization()

from eNMS.app import app
from eNMS.controller import controller


app.init_database()
controller.initialize()

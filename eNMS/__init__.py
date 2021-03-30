from eNMS.app import App
from eNMS.controller import controller

app = App(controller)
app.init_database()

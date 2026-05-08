from eNMS.controller import controller
from eNMS.custom import CustomApp  # noqa: F401
from eNMS.database import db
from eNMS.environment import env
from eNMS.forms import form_factory
from eNMS.models.automation import Run
from eNMS.server import server
from eNMS.variables import vs


def initialize():
    env._initialize()
    if not env.file_watcher:
        server._initialize()
        server.register_plugins()
    first_init = db._initialize(env)
    if env.file_watcher:
        return env.monitor_filesystem()
    if env.detect_cli():
        return
    vs.set_subtypes()
    form_factory._initialize()
    controller._initialize(first_init)
    vs.set_template_context()
    Run._initialize()


initialize()

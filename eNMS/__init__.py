from eNMS.controller import controller
from eNMS.database import db
from eNMS.environment import env
from eNMS.forms import form_factory
from eNMS.variables import vs


def initialize():
    env._initialize()
    first_init = db._initialize(env)
    if env.detect_cli():
        return
    form_factory._initialize()
    controller._initialize(first_init)
    vs._initialize()


initialize()

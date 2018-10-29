from flask import Blueprint

bp = Blueprint(
    'admin_blueprint',
    __name__,
    url_prefix='/admin',
    template_folder='templates',
    static_folder='static'
)

from eNMS.base.models import classes
from eNMS.admin.models import User, Parameters, TacacsServer

classes.update({
    'User': User,
    'Parameters': Parameters,
    'TacacsServer': TacacsServer
})

import eNMS.admin.routes  # noqa: F401

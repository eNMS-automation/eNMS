from flask import Blueprint

bp = Blueprint(
    'admin_blueprint',
    __name__,
    url_prefix='/admin',
    template_folder='templates',
    static_folder='static'
)

from eNMS.base.classes import classes

from eNMS.admin.models import User, Parameters
classes['User'] = User

import eNMS.admin.routes  # noqa: F401

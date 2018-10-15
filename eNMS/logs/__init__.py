from flask import Blueprint

blueprint = Blueprint(
    'logs_blueprint',
    __name__,
    url_prefix='/logs',
    template_folder='templates',
    static_folder='static'
)

import eNMS.logs.routes  # noqa: F401

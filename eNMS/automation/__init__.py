from flask import Blueprint

bp = Blueprint(
    'automation_blueprint',
    __name__,
    url_prefix='/automation',
    template_folder='templates',
    static_folder='static'
)

import eNMS.automation.routes  # noqa: F401

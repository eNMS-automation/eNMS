from flask import Blueprint

blueprint = Blueprint(
    'scheduler_blueprint',
    __name__,
    url_prefix='/scheduler',
    template_folder='templates',
    static_folder='static'
)

import eNMS.scheduler.routes  # noqa: F401

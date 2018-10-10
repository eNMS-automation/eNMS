from flask import Blueprint

blueprint = Blueprint(
    'schedule_blueprint',
    __name__,
    url_prefix='/schedule',
    template_folder='templates',
    static_folder='static'
)

import eNMS.schedule.routes  # noqa: F401

from flask import Blueprint

blueprint = Blueprint(
    'tasks_blueprint',
    __name__,
    url_prefix='/tasks',
    template_folder='templates',
    static_folder='static'
)

import eNMS.tasks.routes  # noqa: F401

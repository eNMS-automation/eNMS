from flask import Blueprint

blueprint = Blueprint(
    'workflows_blueprint',
    __name__,
    url_prefix='/workflows',
    template_folder='templates',
    static_folder='static'
)

import eNMS.workflows.routes  # noqa: F401

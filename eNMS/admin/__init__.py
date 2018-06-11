from flask import Blueprint

blueprint = Blueprint(
    'admin_blueprint',
    __name__,
    url_prefix='/admin',
    template_folder='templates',
    static_folder='static'
)

import eNMS.admin.routes  # noqa: F401

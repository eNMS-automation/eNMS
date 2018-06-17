from flask import Blueprint

blueprint = Blueprint(
    'base_blueprint',
    __name__,
    url_prefix='',
    template_folder='templates'
)

import eNMS.base.routes  # noqa: F401

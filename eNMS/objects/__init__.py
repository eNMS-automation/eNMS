from flask import Blueprint

blueprint = Blueprint(
    'objects_blueprint',
    __name__,
    url_prefix='/objects',
    template_folder='templates',
    static_folder='static'
)

import eNMS.objects.routes  # noqa: F401

from flask import Blueprint

bp = Blueprint(
    'scheduling_blueprint',
    __name__,
    url_prefix='/scheduling',
    template_folder='templates',
    static_folder='static'
)

# import eNMS.scheduling.routes  # noqa: F401

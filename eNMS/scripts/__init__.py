from flask import Blueprint

blueprint = Blueprint(
    'scripts_blueprint',
    __name__,
    url_prefix='/scripts',
    template_folder='templates',
    static_folder='static'
)

from . import routes

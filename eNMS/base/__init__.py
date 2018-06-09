from flask import Blueprint


from eNMS import db


blueprint = Blueprint(
    'base_blueprint',
    __name__,
    url_prefix='',
    template_folder='templates'
)

from . import routes

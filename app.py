from config import config_dict
from eNMS import create_app, db
from flask_migrate import Migrate
from os import environ
from pathlib import Path

get_config_mode = environ.get('ENMS_CONFIG_MODE', 'Production')

try:
    config_mode = config_dict[get_config_mode.capitalize()]
except KeyError:
    sys.exit('Error: Invalid ENMS_CONFIG_MODE environment variable entry.')

app = create_app(Path.cwd(), config_mode)
Migrate(app, db)

from eNMS import create_app, db
from flask_migrate import Migrate
from os.path import abspath, dirname

app = create_app(abspath(dirname(__file__)))
Migrate(app, db)
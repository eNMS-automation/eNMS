from eNMS import create_app, db
from flask_migrate import Migrate

app = create_app()
Migrate(app, db)
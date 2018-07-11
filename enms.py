from eNMS import create_app, db
from flask_migrate import Migrate
from os.path import abspath, dirname
import os


app = create_app(abspath(dirname(__file__)))
Migrate(app, db)

if '__main__' == __name__:
    try:
        if os.environ['FLASK_APP'] is not 'enms.py':
            os.environ['FLASK_APP'] = 'enms.py'
    except KeyError:
        os.environ['FLASK_APP'] = 'enms.py'
    app.run(host='0.0.0.0', port='5000')

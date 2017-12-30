from flask import Flask
from flask_apscheduler import APScheduler
from inspect import stack
from os.path import abspath, dirname, join, pardir
import flask_login
import logging
import os
import sys

# prevent python from writing *.pyc files / __pycache__ folders
sys.dont_write_bytecode = True

path_app = dirname(abspath(stack()[0][1]))
if path_app not in sys.path:
    sys.path.append(path_app)

app = Flask(__name__, static_folder='base/static')
app.config.from_object('config')

path_pynms = os.path.dirname(os.path.abspath(__file__))
path_parent = abspath(join(path_pynms, pardir))
app.path_upload = join(path_parent, 'uploads')
app.path_apps = join(path_parent, 'applications')
app.config['UPLOAD_FOLDER'] = app.path_upload

# start the scheduler
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


# start the login system
login_manager = flask_login.LoginManager()
login_manager.init_app(app)


for name in ('base', 'users', 'objects', 'views', 'automation', 'scheduling'):
    module = __import__(name + '.routes', globals(), locals(), [''])
    app.register_blueprint(module.blueprint)

from base.database import db, init_db
from users.models import User

app.database = db
app.login_manager = login_manager
app.scheduler = scheduler

@login_manager.user_loader
def user_loader(id):
    return db.session.query(User).filter_by(id=id).first()

## tear down SQLAlchemy 

@app.teardown_request
def shutdown_session(exception=None):
    app.database.session.remove()

## Logs

if not app.debug:
    logging.basicConfig(filename='error.log',level=logging.DEBUG)

if __name__ == '__main__':
    init_db()
    
    # returns logger
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())

    # run flask on port 5100
    port = int(os.environ.get('PORT', 5100))
    app.run(host='0.0.0.0', port=port, threaded=True)

from flask import Flask
from flask_apscheduler import APScheduler
from flask_sqlalchemy import SQLAlchemy
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

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
app.database = db

path_pynms = os.path.dirname(os.path.abspath(__file__))
path_parent = abspath(join(path_pynms, pardir))
path_upload = join(path_parent, 'uploads')
path_apps = join(path_parent, 'applications')
app.config['UPLOAD_FOLDER'] = path_upload

# from helpers import *
from models import *
from database import *
from users.models import User

# start the scheduler
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()
app.scheduler = scheduler

# start the login system
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def user_loader(id):
    return db.session.query(User).filter_by(id=id).first()

@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = db.session.query(User).filter_by(username=username).first()
    return user if user else None

for name in ('base', 'users', 'objects', 'views', 'automation', 'scheduling'):
    module = __import__(name + '.routes', globals(), locals(), [''])
    app.register_blueprint(module.blueprint)

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

import os.path as op
from jobs import show_devices
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

basedir = op.abspath(op.dirname(__file__))
DEBUG = True
SECRET_KEY = 'dw)$@(#--dadwa'
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + op.join(basedir, 'database.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

JOBS = [
        {
            'id': 'job10',
            'func': show_devices,
            'trigger': 'interval',
            'seconds': 10,
            'replace_existing': True
        }
        ]

SCHEDULER_JOBSTORES = {
    'default': SQLAlchemyJobStore(url='sqlite:///flask_context.db')
}

SCHEDULER_API_ENABLED = True
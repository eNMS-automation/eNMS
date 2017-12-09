from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import os.path as op

basedir = op.abspath(op.dirname(__file__))
DEBUG = True
SECRET_KEY = 'dw)$@(#--dadwa'

# SQL Alchemy
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + op.join(basedir, 'database.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# # AP Scheduler
JOBS = []
SCHEDULER_JOBSTORES = {'default': SQLAlchemyJobStore(url='sqlite:///flask_context.db')}
SCHEDULER_API_ENABLED = True
# SCHEDULER_EXECUTORS = {
#     'default': {'type': 'threadpool', 'max_workers': 100}
# }
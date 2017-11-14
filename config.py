import os.path as op
basedir = op.abspath(op.dirname(__file__))
DEBUG = True
SECRET_KEY = 'dw)$@(#--dadwa'
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + op.join(basedir, 'database.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False
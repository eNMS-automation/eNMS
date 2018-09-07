from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from os import environ


class Config(object):
    DEBUG = True

    # SQL Alchemy
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db?check_same_thread=False'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # AP Scheduler
    JOBS = []
    SCHEDULER_JOBSTORES = {
        'default': SQLAlchemyJobStore(url='sqlite:///flask_context.db')
    }
    SCHEDULER_API_ENABLED = True
    SCHEDULER_EXECUTORS = {
        'default': {
            'type': 'threadpool',
            'max_workers': 500
        }
    }


class DebugConfig(Config):
    SECRET_KEY = 'key'


class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = environ.get('ENMS_SECRET_KEY')

    # SQL Alchemy
    SQLALCHEMY_DATABASE_URI = (
        environ.get('ENMS_DATABASE_URL') or
        'sqlite:///database.db?check_same_thread=False'
    )

    # Vault
    VAULT_ADDR = environ.get('VAULT_ADDR')
    VAULT_TOKEN = environ.get('VAULT_TOKEN')


class SeleniumConfig(Config):
    DEBUG = True
    TESTING = True
    LOGIN_DISABLED = True
    SECRET_KEY = 'key'


config_dict = {
    'Production': ProductionConfig,
    'Debug': DebugConfig,
    'Selenium': SeleniumConfig
}

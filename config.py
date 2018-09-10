from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from os import environ


class Config(object):

    # SQL Alchemy
    SQLALCHEMY_DATABASE_URI = environ.get(
        'ENMS_DATABASE_URL',
        'sqlite:///database.db?check_same_thread=False'
    )
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
    DEBUG = True
    SECRET_KEY = environ.get('ENMS_SECRET_KEY', 'get-a-real-key')


class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = environ.get('ENMS_SECRET_KEY')

    # Vault
    VAULT_ADDR = environ.get('VAULT_ADDR')
    VAULT_TOKEN = environ.get('VAULT_TOKEN')


class SeleniumConfig(Config):
    DEBUG = True
    SECRET_KEY = 'key'
    TESTING = True
    LOGIN_DISABLED = True


config_dict = {
    'Production': ProductionConfig,
    'Debug': DebugConfig,
    'Selenium': SeleniumConfig
}

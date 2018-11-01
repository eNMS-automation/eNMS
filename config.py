from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from os import environ


class Config(object):
    # SQL Alchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True

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

    # WebSSH (GoTTY)
    GOTTY_PORT_REDIRECTION = int(environ.get('GOTTY_PORT_REDIRECTION', False))
    GOTTY_SERVER_ADDR = environ.get('GOTTY_SERVER_ADDR')
    GOTTY_BYPASS_KEY_PROMPT = environ.get('GOTTY_BYPASS_KEY_PROMPT')

    # Vault
    USE_VAULT = False

    # Examples
    CREATE_EXAMPLES = int(environ.get('CREATE_EXAMPLES', True))

    # Notifications
    # - via Mail
    MAIL_SERVER = environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = int(environ.get('MAIL_USE_TLS', True))
    MAIL_USERNAME = environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = environ.get('MAIL_PASSWORD')


class DebugConfig(Config):
    DEBUG = True
    SECRET_KEY = environ.get('ENMS_SECRET_KEY', 'get-a-real-key')

    # Database
    SQLALCHEMY_DATABASE_URI = environ.get(
        'ENMS_DATABASE_URL',
        'sqlite:///database.db?check_same_thread=False'
    )


class ProductionConfig(Config):
    DEBUG = False
    # In production, the secret MUST be provided as an environment variable.
    SECRET_KEY = environ.get('ENMS_SECRET_KEY')

    # Database
    SQLALCHEMY_DATABASE_URI = environ.get(
        'ENMS_DATABASE_URL',
        'postgresql://{}:{}@{}:{}/{}'.format(
            environ.get('POSTGRES_USER', 'enms'),
            environ.get('POSTGRES_PASSWORD', 'enms'),
            environ.get('POSTGRES_HOST', 'db'),
            environ.get('POSTGRES_PORT', 5432),
            environ.get('POSTGRES_DB', 'enms')
        )
    )

    # Vault
    # In production, all credentials (hashes, usernames and passwords) are
    # stored in a vault.
    # There MUST be a Vault to use eNMS in production mode securely.
    USE_VAULT = int(environ.get('USE_VAULT', True))
    VAULT_ADDR = environ.get('VAULT_ADDR')
    VAULT_TOKEN = environ.get('VAULT_TOKEN')
    UNSEAL_VAULT = environ.get('UNSEAL_VAULT')
    UNSEAL_VAULT_KEY1 = environ.get('UNSEAL_VAULT_KEY1')
    UNSEAL_VAULT_KEY2 = environ.get('UNSEAL_VAULT_KEY2')
    UNSEAL_VAULT_KEY3 = environ.get('UNSEAL_VAULT_KEY3')
    UNSEAL_VAULT_KEY4 = environ.get('UNSEAL_VAULT_KEY4')
    UNSEAL_VAULT_KEY5 = environ.get('UNSEAL_VAULT_KEY5')


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

from os import environ


class Config(object):
    # SQL Alchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True

    # ENMS
    ENMS_SERVER_ADDR = environ.get('ENMS_SERVER_ADDR')

    # WebSSH (GoTTY)
    GOTTY_PORT_REDIRECTION = int(environ.get('GOTTY_PORT_REDIRECTION', False))
    GOTTY_BYPASS_KEY_PROMPT = environ.get('GOTTY_BYPASS_KEY_PROMPT')

    # Vault
    USE_VAULT = int(environ.get('USE_VAULT', False))

    # Gitlab
    GIT_USERNAME = environ.get('GIT_USERNAME')
    GIT_PASSWORD = environ.get('GIT_PASSWORD')

    # LDAP
    LDAP_SERVER = environ.get('LDAP_SERVER')
    LDAP_USERDN = environ.get('LDAP_USERDN')
    LDAP_BASEDN = environ.get('LDAP_BASEDN')

    # TACACS+
    USE_TACACS = int(environ.get('USE_TACACS', False))
    TACACS_ADDR = environ.get('VAULT_ADDR')
    TACACS_PASSWORD = environ.get('VAULT_PASSWORD')

    # Syslog
    USE_SYSLOG = int(environ.get('USE_SYSLOG', False))
    SYSLOG_ADDR = environ.get('SYSLOG_ADDR', '0.0.0.0')
    SYSLOG_PORT = int(environ.get('SYSLOG_PORT', 514))

    # Examples
    CREATE_EXAMPLES = int(environ.get('CREATE_EXAMPLES', True))

    # Custom Services
    CUSTOM_SERVICES_PATH = environ.get('CUSTOM_SERVICES_PATH')

    # Notifications
    # - via Mail
    MAIL_SERVER = environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = int(environ.get('MAIL_USE_TLS', True))
    MAIL_USERNAME = environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = environ.get('MAIL_PASSWORD')

    # Cluster
    # In production, for scalability and high-availability purposes, it is
    # recommended to deploy not one, but multiple instances of eNMS.
    # When a cluster of eNMS is deployed and the "CLUSTER" environment variable
    # is set to "1":
    # - Each request to start an automation job (service or workflow) will be
    # redirected to the least busy eNMS instance (load-balancing). This applies
    # to the requests from the REST API, as well as the requests from the GUI.
    # - When a job is scheduled to run at a later time, it will be replicated
    # to all instances of eNMS so that even if an instance is down, the job
    # will be executed anyway.
    CLUSTER = int(environ.get('CLUSTER', False))


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

    # Security
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600


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

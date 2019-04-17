from os import environ
from typing import Dict, Type


class Config(object):

    # SQL Alchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True

    # ENMS
    ENMS_SERVER_ADDR = environ.get("ENMS_SERVER_ADDR")

    # WebSSH (GoTTY)
    GOTTY_PORT_REDIRECTION = int(environ.get("GOTTY_PORT_REDIRECTION", False))
    GOTTY_BYPASS_KEY_PROMPT = environ.get("GOTTY_BYPASS_KEY_PROMPT")
    GOTTY_START_PORT = int(environ.get("GOTTY_START_PORT", 9000))
    GOTTY_END_PORT = int(environ.get("GOTTY_END_PORT", 9100))

    # Vault
    USE_VAULT = int(environ.get("USE_VAULT", False))

    # LDAP
    LDAP_SERVER = environ.get("LDAP_SERVER")
    LDAP_USERDN = environ.get("LDAP_USERDN")
    LDAP_BASEDN = environ.get("LDAP_BASEDN")
    LDAP_ADMIN_GROUP = environ.get("LDAP_ADMIN_GROUP", "").split(",")

    # TACACS+
    USE_TACACS = int(environ.get("USE_TACACS", False))
    TACACS_ADDR = environ.get("TACACS_ADDR")
    TACACS_PASSWORD = environ.get("TACACS_PASSWORD")

    # Syslog
    USE_SYSLOG = int(environ.get("USE_SYSLOG", False))
    SYSLOG_ADDR = environ.get("SYSLOG_ADDR", "0.0.0.0")
    SYSLOG_PORT = int(environ.get("SYSLOG_PORT", 514))

    # Examples
    CREATE_EXAMPLES = int(environ.get("CREATE_EXAMPLES", True))

    # Custom Services
    CUSTOM_SERVICES_PATH = environ.get("CUSTOM_SERVICES_PATH")

    # Notifications
    # - via Mail
    MAIL_SERVER = environ.get("MAIL_SERVER", "smtp.googlemail.com")
    MAIL_PORT = int(environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = int(environ.get("MAIL_USE_TLS", True))
    MAIL_USERNAME = environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = environ.get("MAIL_PASSWORD")
    MAIL_SENDER = environ.get("MAIL_SENDER", "enms@enms.fr")
    MAIL_RECIPIENTS = environ.get("MAIL_RECIPIENTS", "")

    # - via Mattermost
    MATTERMOST_URL = environ.get("MATTERMOST_URL", "")
    MATTERMOST_CHANNEL = environ.get("MATTERMOST_CHANNEL", "")
    MATTERMOST_VERIFY_CERTIFICATE = int(
        environ.get("MATTERMOST_VERIFY_CERTIFICATE", True)
    )

    # - Via Slack
    SLACK_TOKEN = environ.get("SLACK_TOKEN", "")
    SLACK_CHANNEL = environ.get("SLACK_CHANNEL", "")

    # Logging
    ENMS_LOG_LEVEL = environ.get("ENMS_LOG_LEVEL", "DEBUG").upper()

    # Cluster
    # In production, for scalability and high-availability purposes, it is
    # recommended to deploy not one, but multiple instances of eNMS.
    CLUSTER = int(environ.get("CLUSTER", False))
    CLUSTER_ID = int(environ.get("CLUSTER_ID", True))
    CLUSTER_SCAN_SUBNET = environ.get("CLUSTER_SCAN_SUBNET", "192.168.105.0/24")
    CLUSTER_SCAN_PROTOCOL = environ.get("CLUSTER_SCAN_PROTOCOL", "http")
    CLUSTER_SCAN_TIMEOUT = float(environ.get("CLUSTER_SCAN_TIMEOUT", 0.05))

    # Geographical Parameters
    DEFAULT_LONGITUDE = float(environ.get("DEFAULT_LONGITUDE", -96.0))
    DEFAULT_LATITUDE = float(environ.get("DEFAULT_LATITUDE", 33.0))
    DEFAULT_ZOOM_LEVEL = int(environ.get("DEFAULT_ZOOM_LEVEL", 5))
    DEFAULT_VIEW = environ.get("DEFAULT_VIEW", "2D")
    DEFAULT_MARKER = environ.get("DEFAULT_MARKER", "Image")

    # Git Parameters
    GIT_AUTOMATION = environ.get("GIT_AUTOMATION", "")
    GIT_CONFIGURATIONS = environ.get("GIT_CONFIGURATIONS", "")

    # Pool Filter Parameter
    POOL_FILTER = environ.get("POOL_FILTER", "All objects")


class DebugConfig(Config):
    DEBUG = True
    SECRET_KEY = environ.get("ENMS_SECRET_KEY", "get-a-real-key")

    # Database
    SQLALCHEMY_DATABASE_URI = environ.get(
        "ENMS_DATABASE_URL", "sqlite:///database.db?check_same_thread=False"
    )

    # Mail
    MAIL_DEBUG = 1


class ProductionConfig(Config):
    DEBUG = False
    # In production, the secret MUST be provided as an environment variable.
    SECRET_KEY = environ.get("ENMS_SECRET_KEY")

    # Database
    SQLALCHEMY_DATABASE_URI = environ.get(
        "ENMS_DATABASE_URL",
        "postgresql://{}:{}@{}:{}/{}".format(
            environ.get("POSTGRES_USER", "enms"),
            environ.get("POSTGRES_PASSWORD", "enms"),
            environ.get("POSTGRES_HOST", "db"),
            environ.get("POSTGRES_PORT", 5432),
            environ.get("POSTGRES_DB", "enms"),
        ),
    )

    # Vault
    # In production, all credentials (hashes, usernames and passwords) are
    # stored in a vault.
    # There MUST be a Vault to use eNMS in production mode securely.
    USE_VAULT = int(environ.get("USE_VAULT", True))
    VAULT_ADDR = environ.get("VAULT_ADDR")
    VAULT_TOKEN = environ.get("VAULT_TOKEN")
    UNSEAL_VAULT = environ.get("UNSEAL_VAULT")
    UNSEAL_VAULT_KEY1 = environ.get("UNSEAL_VAULT_KEY1")
    UNSEAL_VAULT_KEY2 = environ.get("UNSEAL_VAULT_KEY2")
    UNSEAL_VAULT_KEY3 = environ.get("UNSEAL_VAULT_KEY3")
    UNSEAL_VAULT_KEY4 = environ.get("UNSEAL_VAULT_KEY4")
    UNSEAL_VAULT_KEY5 = environ.get("UNSEAL_VAULT_KEY5")

    # Security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600


config_dict: Dict[str, Type[Config]] = {
    "Production": ProductionConfig,
    "Debug": DebugConfig,
}

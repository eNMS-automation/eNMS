from os import environ
from typing import Dict, Type


class Config(object):

    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = environ.get("MAIL_SERVER", "smtp.googlemail.com")
    MAIL_PORT = int(environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = int(environ.get("MAIL_USE_TLS", True))
    MAIL_USERNAME = environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = environ.get("MAIL_PASSWORD")
    MAIL_SENDER = environ.get("MAIL_SENDER", "enms@enms.fr")
    MAIL_RECIPIENTS = environ.get("MAIL_RECIPIENTS", "")


class DebugConfig(Config):
    DEBUG = True
    SECRET_KEY = environ.get("ENMS_SECRET_KEY", "get-a-real-key")
    SQLALCHEMY_DATABASE_URI = environ.get(
        "ENMS_DATABASE_URL", "sqlite:///database.db?check_same_thread=False"
    )
    MAIL_DEBUG = 1
    DEBUG_TB_PROFILER_ENABLED = False


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

    # Security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600


class TestConfig(DebugConfig):
    WTF_CSRF_ENABLED = False


config_dict: Dict[str, Type[Config]] = {
    "Debug": DebugConfig,
    "Production": ProductionConfig,
    "Test": TestConfig,
}

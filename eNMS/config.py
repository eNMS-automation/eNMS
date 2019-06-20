from os import environ


class DefaultConfig:
    MODE = "default"
    DEBUG = True
    SECRET_KEY = environ.get("ENMS_SECRET_KEY", "get-a-real-key")
    WTF_CSRF_TIME_LIMIT = None
    ERROR_404_HELP = False


class ProductionConfig:
    MODE = "production"
    DEBUG = False
    SECRET_KEY = environ.get("ENMS_SECRET_KEY")
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600


class TestConfig(DefaultConfig):
    MODE = "test"
    WTF_CSRF_ENABLED = False


config_mapper: dict = {
    "Default": DefaultConfig,
    "Production": ProductionConfig,
    "Test": TestConfig,
}

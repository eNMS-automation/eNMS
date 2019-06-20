from os import environ


class DefaultConfig:
    MODE = "default"
    DEBUG = True
    SECRET_KEY = environ.get("ENMS_SECRET_KEY", "get-a-real-key")
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_CHECK_DEFAULT = False
    DEBUG_TB_ENABLED = False
    ERROR_404_HELP = False


class DevelopConfig(DefaultConfig):
    MODE = "develop"
    DEVELOP = True
    DEBUG_TB_ENABLED = True
    DEBUG_TB_PROFILER_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False


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
    "Develop": DevelopConfig,
    "Production": ProductionConfig,
    "Test": TestConfig,
}

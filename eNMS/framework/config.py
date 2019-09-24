from os import environ


class DebugConfig:
    MODE = "debug"
    DEBUG = True
    JSON_SORT_KEYS = False
    SECRET_KEY = environ.get("SECRET_KEY", "get-a-real-key")
    WTF_CSRF_TIME_LIMIT = None
    ERROR_404_HELP = False
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024


class ProductionConfig:
    MODE = "production"
    DEBUG = False
    SECRET_KEY = environ.get("SECRET_KEY")
    WTF_CSRF_TIME_LIMIT = None


class TestConfig(DebugConfig):
    MODE = "test"
    WTF_CSRF_ENABLED = False


config_mapper = {
    "Debug": DebugConfig,
    "Production": ProductionConfig,
    "Test": TestConfig,
}

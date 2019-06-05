from os import environ
from typing import Dict, Type


class Config(object):
    CACHE_TYPE = "simple"


class DefaultConfig(Config):
    MODE = "default"
    DEBUG = True
    SECRET_KEY = environ.get("ENMS_SECRET_KEY", "get-a-real-key")
    MAIL_DEBUG = 1
    DEBUG_TB_ENABLED = False


class DevelopConfig(DefaultConfig):
    MODE = "develop"
    DEVELOP = True
    DEBUG_TB_ENABLED = True
    DEBUG_TB_PROFILER_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False


class ProductionConfig(Config):
    MODE = "production"
    DEBUG = False
    SECRET_KEY = environ.get("ENMS_SECRET_KEY")
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600


class TestConfig(DefaultConfig):
    MODE = "test"
    CACHE_TYPE = "null"
    WTF_CSRF_ENABLED = False


config_mapper: Dict[str, Type[Config]] = {
    "Default": DefaultConfig,
    "Develop": DevelopConfig,
    "Production": ProductionConfig,
    "Test": TestConfig,
}

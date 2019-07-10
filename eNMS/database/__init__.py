from decimal import Decimal
from flask.json import JSONEncoder
from os import environ
from sqlalchemy import create_engine, PickleType
from sqlalchemy.dialects.mysql.base import MSMediumBlob
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from typing import Any


DATABASE_URL = environ.get(
    "ENMS_DATABASE_URL", "sqlite:///database.db?check_same_thread=False"
)
DIALECT = DATABASE_URL.split(":")[0]
SMALL_STRING_LENGTH = int(environ.get("SMALL_STRING_LENGTH", 255))
LARGE_STRING_LENGTH = int(environ.get("LARGE_STRING_LENGTH", 2 ** 15))


def session_factory() -> Any:
    kwargs = {}
    if DIALECT == "mysql":
        kwargs.update(
            {
                "max_overflow": int(environ.get("MAX_OVERFLOW", 10)),
                "pool_size": int(environ.get("POOL_SIZE", 1000)),
            }
        )
    engine = create_engine(
        environ.get(
            "ENMS_DATABASE_URL", "sqlite:///database.db?check_same_thread=False"
        ),
        convert_unicode=True,
        pool_pre_ping=True,
        **kwargs
    )
    return engine, scoped_session(sessionmaker(autoflush=False, bind=engine))


engine, Session = session_factory()
Base = declarative_base()


class CustomMediumBlobPickle(PickleType):
    if DIALECT == "mysql":
        impl = MSMediumBlob


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)

from os import environ
from sqlalchemy import create_engine, PickleType
from sqlalchemy.dialects.mysql.base import MSMediumBlob
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from typing import Any


def session_factory() -> Any:
    engine = create_engine(
        environ.get(
            "ENMS_DATABASE_URL", "sqlite:///database.db?check_same_thread=False"
        ),
        max_overflow=int(environ.get("MAX_OVERFLOW", 10)),
        convert_unicode=True,
        pool_pre_ping=True,
        pool_size=int(environ.get("POOL_SIZE", 1000)),
    )
    return engine, scoped_session(sessionmaker(autoflush=False, bind=engine))


engine, Session = session_factory()
dialect = Session.bind.dialect.name

Base = declarative_base()

SMALL_STRING_LENGTH = int(environ.get("SMALL_STRING_LENGTH", 255))
LARGE_STRING_LENGTH = int(environ.get("LARGE_STRING_LENGTH", 2 ** 15))


class CustomMediumBlobPickle(PickleType):
    if dialect == "mysql":
        impl = MSMediumBlob

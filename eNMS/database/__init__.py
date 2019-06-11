from os import environ
from sqlalchemy import create_engine, PickleType
from sqlalchemy.dialects.mysql.base import MSMediumBlob
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker


engine = create_engine(
    environ.get("ENMS_DATABASE_URL", "sqlite:///database.db?check_same_thread=False"),
    convert_unicode=True,
    pool_pre_ping=True,
)

Session = scoped_session(sessionmaker(autoflush=False, bind=engine))
dialect = Session.bind.dialect.name

Base = declarative_base()

SMALL_STRING_LENGTH = int(environ.get("SMALL_STRING_LENGTH", 255))
LARGE_STRING_LENGTH = int(environ.get("LARGE_STRING_LENGTH", 2 ** 10))


class CustomMediumBlobPickle(PickleType):
    if dialect == "mysql":
        impl = MSMediumBlob

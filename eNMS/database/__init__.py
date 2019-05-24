from os import environ
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker


engine = create_engine(
    environ.get("ENMS_DATABASE_URL", "sqlite:///database.db?check_same_thread=False"),
    convert_unicode=True,
    pool_pre_ping=True,
)

Session = scoped_session(
    sessionmaker(expire_on_commit=False, autoflush=False, bind=engine)
)

Base = declarative_base()

SMALL_STRING_LENGTH = int(environ.get("SMALL_STRING_LENGTH", 255))
LARGE_STRING_LENGTH = int(environ.get("LARGE_STRING_LENGTH", 2 ** 10))

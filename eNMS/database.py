from sqlalchemy import create_engine, exc
from sqlalchemy.ext.declarative import declarative_base

from eNMS.database_helpers import engine

Base = declarative_base()


def init_db():
    Base.metadata.create_all(bind=engine)

from sqlalchemy import create_engine, exc
from sqlalchemy.ext.declarative import declarative_base

from eNMS.database_helpers import engine

SQLBase = declarative_base()


def init_db():
    from eNMS.models.administration import Server, User
    from eNMS.models.inventory import Device, Link, Pool

    SQLBase.metadata.create_all(bind=engine)

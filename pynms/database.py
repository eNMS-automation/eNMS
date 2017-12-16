from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from base.helpers import napalm_dispatcher
from main import db

engine = create_engine('sqlite:///database.db', convert_unicode=True, echo=True)
db.session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

Base = declarative_base()
Base.query = db.session.query_property()

def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.
    import models
    Base.metadata.create_all(bind=engine)

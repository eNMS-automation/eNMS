from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from helpers import napalm_dispatcher
from app import db

engine = create_engine('sqlite:///database.db', convert_unicode=True, echo=True)
db.session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

Base = declarative_base()
Base.query = db.session.query_property()

def clear_db():
    import models
    models.Device.query.delete()
    db.session.commit()

def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import models
    Base.metadata.create_all(bind=engine)
    
    # add all devices to the database
    db.session.query(models.Device).delete()
    db.session.commit()
    for hostname, (IP, OS) in napalm_dispatcher.items():
        device = models.Device(hostname, IP, OS)
        db.session.add(device)
    db.session.commit()

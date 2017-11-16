from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from helpers import napalm_dispatcher
from app import db
import sys
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
    db.session.query(models.Department).delete()
    db.session.query(models.Employee).delete()
    db.session.commit()
    for hostname, (IP, OS) in napalm_dispatcher.items():
        device = models.Device(hostname, IP, OS)
        db.session.add(device)
    db.session.commit()
    
    # employee for jquery test
    for dep, employees in {'a': ('1', '2'), 'b': ('3', '4'), 'c': ('i',)}.items():
        department = models.Department(dep)
        db.session.add(department)
        db.session.flush()
        for employee in employees:
            e = models.Employee(employee, department.id)
            db.session.add(e)
    db.session.commit()
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from eNMS.setup import settings

class Database:

    def __init__(self):
        self.database_url = settings["database"]["url"]
        self.dialect = self.database_url.split(":")[0]
        self.engine = self.configure_engine()
        self.session = Session = scoped_session(sessionmaker(autoflush=False, bind=self.engine))
        self.base = declarative_base()

    def configure_engine(self):
        engine_parameters = {
            "convert_unicode": True,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        }
        if self.dialect == "mysql":
            engine_parameters.update(
                {
                    "max_overflow": settings["database"]["max_overflow"],
                    "pool_size": settings["database"]["pool_size"],
                }
            )
        return create_engine(self.database_url, **engine_parameters)

db = Database()

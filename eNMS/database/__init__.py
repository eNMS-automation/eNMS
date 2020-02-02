from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from eNMS.settings import settings

DATABASE_URL = settings["database"]["url"]
DIALECT = DATABASE_URL.split(":")[0]

engine_parameters = {
    "convert_unicode": True,
    "pool_pre_ping": True,
    "pool_recycle": 3600,
}

if DIALECT == "mysql":
    engine_parameters.update(
        {
            "max_overflow": settings["database"]["max_overflow"],
            "pool_size": settings["database"]["pool_size"],
        }
    )

engine = create_engine(DATABASE_URL, **engine_parameters)
Session = scoped_session(sessionmaker(autoflush=False, bind=engine))
Base = declarative_base()

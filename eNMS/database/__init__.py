from sqlalchemy import Column, create_engine, ForeignKey, Integer, Table
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
        self.configure_associations()

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

    def configure_associations(self):

        self.service_device_table = Table(
            "service_device_association",
            self.base.metadata,
            Column("device_id", Integer, ForeignKey("device.id")),
            Column("service_id", Integer, ForeignKey("service.id")),
        )

        self.service_pool_table = Table(
            "service_pool_association",
            self.base.metadata,
            Column("pool_id", Integer, ForeignKey("pool.id")),
            Column("service_id", Integer, ForeignKey("service.id")),
        )

        self.run_device_table = Table(
            "run_device_association",
            self.base.metadata,
            Column("device_id", Integer, ForeignKey("device.id")),
            Column("run_id", Integer, ForeignKey("run.id", ondelete="cascade")),
        )

        self.run_pool_table = Table(
            "run_pool_association",
            self.base.metadata,
            Column("pool_id", Integer, ForeignKey("pool.id")),
            Column("run_id", Integer, ForeignKey("run.id", ondelete="cascade")),
        )

        self.task_device_table = Table(
            "task_device_association",
            self.base.metadata,
            Column("device_id", Integer, ForeignKey("device.id")),
            Column("task_id", Integer, ForeignKey("task.id")),
        )

        self.task_pool_table = Table(
            "task_pool_association",
            self.base.metadata,
            Column("pool_id", Integer, ForeignKey("pool.id")),
            Column("task_id", Integer, ForeignKey("task.id")),
        )

        self.service_workflow_table = Table(
            "service_workflow_association",
            self.base.metadata,
            Column("service_id", Integer, ForeignKey("service.id")),
            Column("workflow_id", Integer, ForeignKey("workflow.id")),
        )

        self.pool_device_table = Table(
            "pool_device_association",
            self.base.metadata,
            Column("pool_id", Integer, ForeignKey("pool.id")),
            Column("device_id", Integer, ForeignKey("device.id")),
        )

        self.pool_link_table = Table(
            "pool_link_association",
            self.base.metadata,
            Column("pool_id", Integer, ForeignKey("pool.id")),
            Column("link_id", Integer, ForeignKey("link.id")),
        )

db = Database()

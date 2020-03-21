from sqlalchemy import Column, ForeignKey, Integer, Table

from eNMS.database import db

service_device_table = Table(
    "service_device_association",
    db.base.metadata,
    Column("device_id", Integer, ForeignKey("device.id")),
    Column("service_id", Integer, ForeignKey("service.id")),
)

service_pool_table = Table(
    "service_pool_association",
    db.base.metadata,
    Column("pool_id", Integer, ForeignKey("pool.id")),
    Column("service_id", Integer, ForeignKey("service.id")),
)

run_device_table = Table(
    "run_device_association",
    db.base.metadata,
    Column("device_id", Integer, ForeignKey("device.id")),
    Column("run_id", Integer, ForeignKey("run.id", ondelete="cascade")),
)

run_pool_table = Table(
    "run_pool_association",
    db.base.metadata,
    Column("pool_id", Integer, ForeignKey("pool.id")),
    Column("run_id", Integer, ForeignKey("run.id", ondelete="cascade")),
)

task_device_table = Table(
    "task_device_association",
    db.base.metadata,
    Column("device_id", Integer, ForeignKey("device.id")),
    Column("task_id", Integer, ForeignKey("task.id")),
)

task_pool_table = Table(
    "task_pool_association",
    db.base.metadata,
    Column("pool_id", Integer, ForeignKey("pool.id")),
    Column("task_id", Integer, ForeignKey("task.id")),
)

service_workflow_table = Table(
    "service_workflow_association",
    db.base.metadata,
    Column("service_id", Integer, ForeignKey("service.id")),
    Column("workflow_id", Integer, ForeignKey("workflow.id")),
)

pool_device_table = Table(
    "pool_device_association",
    db.base.metadata,
    Column("pool_id", Integer, ForeignKey("pool.id")),
    Column("device_id", Integer, ForeignKey("device.id")),
)

pool_link_table = Table(
    "pool_link_association",
    db.base.metadata,
    Column("pool_id", Integer, ForeignKey("pool.id")),
    Column("link_id", Integer, ForeignKey("link.id")),
)

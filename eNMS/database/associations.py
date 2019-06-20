from sqlalchemy import Column, ForeignKey, Integer, Table

from eNMS.database import Base

job_device_table: Table = Table(
    "job_device_association",
    Base.metadata,
    Column("device_id", Integer, ForeignKey("Device.id")),
    Column("job_id", Integer, ForeignKey("Job.id")),
)

job_pool_table: Table = Table(
    "job_pool_association",
    Base.metadata,
    Column("pool_id", Integer, ForeignKey("Pool.id")),
    Column("job_id", Integer, ForeignKey("Job.id")),
)

task_device_table: Table = Table(
    "task_device_association",
    Base.metadata,
    Column("device_id", Integer, ForeignKey("Device.id")),
    Column("task_id", Integer, ForeignKey("Task.id")),
)

task_pool_table: Table = Table(
    "task_pool_association",
    Base.metadata,
    Column("pool_id", Integer, ForeignKey("Pool.id")),
    Column("task_id", Integer, ForeignKey("Task.id")),
)

event_log_table: Table = Table(
    "event_log_association",
    Base.metadata,
    Column("log_id", Integer, ForeignKey("Log.id")),
    Column("event_id", Integer, ForeignKey("Event.id")),
)

job_event_table: Table = Table(
    "job_event_association",
    Base.metadata,
    Column("job_id", Integer, ForeignKey("Job.id")),
    Column("event_id", Integer, ForeignKey("Event.id")),
)

job_workflow_table: Table = Table(
    "job_workflow_association",
    Base.metadata,
    Column("job_id", Integer, ForeignKey("Job.id")),
    Column("workflow_id", Integer, ForeignKey("Workflow.id")),
)

pool_device_table: Table = Table(
    "pool_device_association",
    Base.metadata,
    Column("pool_id", Integer, ForeignKey("Pool.id")),
    Column("device_id", Integer, ForeignKey("Device.id")),
)

pool_link_table: Table = Table(
    "pool_link_association",
    Base.metadata,
    Column("pool_id", Integer, ForeignKey("Pool.id")),
    Column("link_id", Integer, ForeignKey("Link.id")),
)

pool_user_table: Table = Table(
    "pool_user_association",
    Base.metadata,
    Column("pool_id", Integer, ForeignKey("Pool.id")),
    Column("user_id", Integer, ForeignKey("User.id")),
)

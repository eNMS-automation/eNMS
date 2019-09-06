from sqlalchemy import Column, ForeignKey, Integer, Table

from eNMS.database import Base

job_device_table: Table = Table(
    "job_device_association",
    Base.metadata,
    Column("device_id", Integer, ForeignKey("device.id")),
    Column("job_id", Integer, ForeignKey("job.id")),
)

job_pool_table: Table = Table(
    "job_pool_association",
    Base.metadata,
    Column("pool_id", Integer, ForeignKey("Pool.id")),
    Column("job_id", Integer, ForeignKey("job.id")),
)

task_device_table: Table = Table(
    "task_device_association",
    Base.metadata,
    Column("device_id", Integer, ForeignKey("device.id")),
    Column("task_id", Integer, ForeignKey("Task.id")),
)

task_pool_table: Table = Table(
    "task_pool_association",
    Base.metadata,
    Column("pool_id", Integer, ForeignKey("Pool.id")),
    Column("task_id", Integer, ForeignKey("Task.id")),
)

job_event_table: Table = Table(
    "job_event_association",
    Base.metadata,
    Column("job_id", Integer, ForeignKey("job.id")),
    Column("event_id", Integer, ForeignKey("Event.id")),
)

job_workflow_table: Table = Table(
    "job_workflow_association",
    Base.metadata,
    Column("job_id", Integer, ForeignKey("job.id")),
    Column("workflow_id", Integer, ForeignKey("workflow.id")),
)

start_jobs_workflow_table: Table = Table(
    "start_jobs_workflow_association",
    Base.metadata,
    Column("job_id", Integer, ForeignKey("job.id")),
    Column("workflow_id", Integer, ForeignKey("workflow.id")),
)

pool_device_table: Table = Table(
    "pool_device_association",
    Base.metadata,
    Column("pool_id", Integer, ForeignKey("Pool.id")),
    Column("device_id", Integer, ForeignKey("device.id")),
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

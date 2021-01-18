from flask_login import current_user
from functools import wraps
from requests import get, post
from requests.exceptions import ConnectionError, MissingSchema, ReadTimeout
from sqlalchemy import Boolean, case, ForeignKey, Integer
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import aliased, relationship

from eNMS import app
from eNMS.database import db
from eNMS.models import models
from eNMS.models.base import AbstractBase


class Task(AbstractBase):

    __tablename__ = type = "task"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    default_access = db.Column(db.SmallString)
    description = db.Column(db.LargeString)
    creator = db.Column(db.SmallString)
    last_scheduled_by = db.Column(db.SmallString)
    scheduling_mode = db.Column(db.TinyString, default="standard")
    frequency = db.Column(Integer)
    frequency_unit = db.Column(db.TinyString, default="seconds")
    start_date = db.Column(db.TinyString)
    end_date = db.Column(db.TinyString)
    crontab_expression = db.Column(db.TinyString)
    is_active = db.Column(Boolean, default=False)
    initial_payload = db.Column(db.Dict)
    devices = relationship(
        "Device", secondary=db.task_device_table, back_populates="tasks"
    )
    pools = relationship("Pool", secondary=db.task_pool_table, back_populates="tasks")
    service_id = db.Column(Integer, ForeignKey("service.id"))
    service = relationship("Service", back_populates="tasks")
    service_name = association_proxy("service", "name")
    model_properties = ["next_run_time", "time_before_next_run", "status"]

    def update(self, **kwargs):
        super().update(**kwargs)
        db.session.commit()
        self.schedule(mode="schedule" if self.is_active else "pause")

    def delete(self):
        post(f"{app.scheduler_address}/delete_job/{self.id}")

    @hybrid_property
    def status(self):
        return "Active" if self.is_active else "Inactive"

    @status.expression
    def status(cls):  # noqa: N805
        return case([(cls.is_active, "Active")], else_="Inactive")

    @classmethod
    def rbac_filter(cls, query, mode, user):
        query = query.filter(cls.default_access != "admin")
        public_tasks = query.join(cls.service).filter(
            models["service"].default_access == "public"
        )
        pool_alias = aliased(models["pool"])
        return public_tasks.union(
            query.join(cls.service)
            .join(models["pool"], models["service"].pools)
            .join(models["access"], models["pool"].access)
            .join(pool_alias, models["access"].user_pools)
            .join(models["user"], pool_alias.users)
            .filter(models["access"].access_type.contains(mode))
            .filter(models["user"].name == user.name),
            query.filter(cls.creator == user.name),
        )

    def _catch_request_exceptions(func):  # noqa: N805
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except (ConnectionError, MissingSchema, ReadTimeout):
                return "Scheduler Unreachable"
            except Exception as exc:
                return f"Error ({exc})"

        return wrapper

    @property
    @_catch_request_exceptions
    def next_run_time(self):
        return get(
            f"{app.scheduler_address}/next_runtime/{self.id}", timeout=0.01
        ).json()

    @property
    @_catch_request_exceptions
    def time_before_next_run(self):
        return get(f"{app.scheduler_address}/time_left/{self.id}", timeout=0.01).json()

    @_catch_request_exceptions
    def schedule(self, mode="schedule"):
        try:
            payload = {"mode": mode, "task": self.get_properties()}
            result = post(f"{app.scheduler_address}/schedule", json=payload).json()
            self.last_scheduled_by = current_user.name
        except ConnectionError:
            return {"alert": "Scheduler Unreachable: the task cannot be scheduled."}
        self.is_active = result.get("active", False)
        return result

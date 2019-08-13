from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship
from typing import Optional
from wtforms import BooleanField, HiddenField, SelectField, StringField

from eNMS.concurrency import run_job
from eNMS.controller import controller
from eNMS.database import SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import DictField, InstanceField
from eNMS.models.automation import Run, Service
from eNMS.models.inventory import Device


class IterationService(Service):

    __tablename__ = "IterationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = Column(Boolean, default=False)
    iterated_job_id = Column(Integer, ForeignKey("Job.id"))
    iterated_job = relationship(
        "Job", primaryjoin="Job.id == IterationService.iterated_job_id"
    )
    origin_of_values = Column(
        SmallString, default="user_provided_values"
    )
    python_query_values = Column(SmallString, default="")
    user_provided_values = Column(MutableDict, default={})
    conversion_property = Column(SmallString, default="name")
    variable_name = Column(SmallString, default="value")

    __mapper_args__ = {"polymorphic_identity": "IterationService"}

    def get_properties(self, *args):
        return {"iterated_job": self.iterated_job.name, **super().get_properties(*args)}

    def job(self, run: "Run", payload: dict, device: Optional[Device] = None) -> dict:
        if run.origin_of_values == "user_provided_values":
            if device.name in run.user_provided_values:
                values = run.user_provided_values[device.name]
            else:
                values = run.user_provided_values["all"]
        else:
            values = controller.eval(run.python_query_values, run, **locals())
        results, success = {}, True
        for value in values:
            run_data = {
                "payload": {self.variable_name: value, **payload},
                "devices": [device.id],
            }
            result = run_job(self.iterated_job.id, **run_data)
            results[value] = result["results"]["devices"][device.name]
            if not result["success"]:
                success = False
        return {"success": success, "Iteration values": values, **results}


class IterationForm(ServiceForm):
    form_type = HiddenField(default="IterationService")
    has_targets = BooleanField("Has Target Devices")
    origin_of_values = SelectField(
        "Where Values come from",
        choices=(
            ("user_provided_values", "User-provided Values (dictionary)"),
            ("python_query", "Python Query on the Payload"),
        ),
    )
    user_provided_values = DictField(
        "Iteration Values for Iteration: User provided "
        "(Expect dictionary {'all' : [...]} or {'device-name' : [...], ...})"
    )
    python_query_values = StringField(
        "Iteration Values for Iteration: Python query on the payload"
    )
    variable_name = StringField("Iteration Variable Name")
    iterated_job = InstanceField("Job to run for each Value", instance_type="Job")

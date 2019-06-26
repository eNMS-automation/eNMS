from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship
from typing import Optional, Set
from wtforms import BooleanField, HiddenField, SelectField, StringField
from yaql import factory

from eNMS.database import SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import DictField, InstanceField
from eNMS.models.automation import Job, Service
from eNMS.models.inventory import Device


class IterationService(Service):

    __tablename__ = "IterationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = Column(Boolean, default=False)
    iterated_job_id = Column(Integer, ForeignKey("Job.id"))
    iterated_job = relationship(
        "Job", primaryjoin="Job.id == IterationService.iterated_job_id"
    )
    origin_of_values = Column(String(SMALL_STRING_LENGTH), default="iteration_values")
    yaql_query_values = Column(String(SMALL_STRING_LENGTH), default="")
    iteration_values = Column(MutableDict.as_mutable(PickleType), default={})
    variable_name = Column(String(SMALL_STRING_LENGTH), default="value")
    per_device_values = Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "IterationService"}

    def get_properties(self, *args):
        return {"iterated_job": self.iterated_job.name, **super().get_properties(*args)}

    def job(
        self,
        payload: dict,
        device: Optional[Device] = None,
        parent: Optional[Job] = None,
    ) -> dict:
        if self.origin_of_values == "iteration_values":
            values = self.iteration_values.get(device.name if self.per_device_values else "all")
        else:
            query = self.sub(self.yaql_query_values, locals())
            values = factory.YaqlFactory().create()(query).evaluate(data=payload)
        results = {
            value: self.iterated_job.job({self.variable_name: value, **payload}, device)
            for value in values
        }
        return {"success": True, "Iteration values": values, **results}


class IterationForm(ServiceForm):
    form_type = HiddenField(default="IterationService")
    has_targets = BooleanField()
    origin_of_targets = SelectField(
        choices=(
            ("iteration", "Use Targets from Iteration Service"),
            ("iterated", "Use Targets from Iterated Service"),
        )
    )
    origin_of_values = SelectField(
        choices=(
            ("iteration_values", "Iteration Values Dictionary below"),
            ("yaql", "YaQL Query on the Payload"),
        )
    )
    iteration_values = DictField()
    yaql_query_values = StringField()
    per_device_values = BooleanField()
    variable_name = StringField("Name of the Variable in the Payload")
    iterated_job = InstanceField("What Job to Iterate", instance_type="Job")

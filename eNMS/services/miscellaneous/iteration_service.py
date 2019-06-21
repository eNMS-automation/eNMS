from sqlalchemy import Column, ForeignKey, Integer, PickleType
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy import Boolean, case, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import backref, relationship
from wtforms import BooleanField, HiddenField, IntegerField, SelectField, StringField

from eNMS.database import LARGE_STRING_LENGTH, SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import DictField, InstanceField
from eNMS.models.automation import Service


class IterationService(Service):

    __tablename__ = "IterationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = False
    iterated_job_id = Column(Integer, ForeignKey("Job.id"))
    iterated_job = relationship(
        "Job", primaryjoin="Job.id == IterationService.iterated_job_id"
    )
    origin_of_targets = Column(String(SMALL_STRING_LENGTH), default="iteration")
    iteration_values = Column(MutableDict.as_mutable(PickleType), default={})

    __mapper_args__ = {"polymorphic_identity": "IterationService"}

    def job(self, payload: dict) -> dict:
        devices = self.compute_devices() if self.origin_of_targets == "iteration" else self.iterated_job.devices
        payload[self.name] = self.iteration_values
        results, _ = self.job.run(payload, devices, self)
        return {"success": True, "result": results}


class IterationForm(ServiceForm):
    form_type = HiddenField(default="IterationService")
    iterated_job = InstanceField("Iterated Job", instance_type="Job")
    origin_of_targets = SelectField(
        choices=(
            ("iteration", "Use Targets from Iteration Service"),
            ("iterated", "Use Targets from Iterated Service"),
        )
    )
    iteration_values = DictField()

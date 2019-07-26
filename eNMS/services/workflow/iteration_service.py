from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship
from typing import Optional
from wtforms import BooleanField, HiddenField, SelectField, StringField

from eNMS.database import SMALL_STRING_LENGTH
from eNMS.database.functions import fetch
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
    origin_of_values = Column(
        String(SMALL_STRING_LENGTH), default="user_provided_values"
    )
    python_query_values = Column(String(SMALL_STRING_LENGTH), default="")
    user_provided_values = Column(MutableDict.as_mutable(PickleType), default={})
    convert_values_to_devices = Column(Boolean, default=False)
    conversion_property = Column(String(SMALL_STRING_LENGTH), default="name")
    variable_name = Column(String(SMALL_STRING_LENGTH), default="value")

    __mapper_args__ = {"polymorphic_identity": "IterationService"}

    def get_properties(self, *args):
        return {"iterated_job": self.iterated_job.name, **super().get_properties(*args)}

    def job(
        self,
        payload: dict,
        timestamp: str,
        device: Optional[Device] = None,
        parent: Optional[Job] = None,
    ) -> dict:
        if self.origin_of_values == "user_provided_values":
            if device.name in self.user_provided_values:
                values = self.user_provided_values[device.name]
            else:
                values = self.user_provided_values["all"]
        else:
            values = eval(self.python_query_values, locals())
        if self.convert_values_to_devices:
            fail_results, devices = {}, set()
            for value in values:
                device = fetch(
                    "Device", allow_none=True, **{self.conversion_property: value}
                )
                if not device:
                    fail_results[value] = {
                        "result": "Error: no corresponding device",
                        "success": False,
                    }
                else:
                    devices.add(device)
            results = self.iterated_job.run(
                payload=payload, targets=devices, parent=parent or self
            )[0]
            if fail_results:
                results["results"]["devices"].update(fail_results)
                results["success"] = False
            success = results["success"]
        else:
            results, success = {}, True
            for value in values:
                result = self.iterated_job.job(
                    {self.variable_name: value, **payload}, device
                )
                results[value] = result
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
    convert_values_to_devices = BooleanField("Convert values to devices")
    conversion_property = SelectField(
        "Property used for the conversion to devices",
        choices=(("name", "Name"), ("ip_address", "IP address")),
    )
    variable_name = StringField("Iteration Variable Name")
    iterated_job = InstanceField("Job to run for each Value", instance_type="Job")

from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship
from typing import Optional
from wtforms import BooleanField, HiddenField, SelectField, StringField
from yaql import factory

from eNMS.database import SMALL_STRING_LENGTH
from eNMS.database.functions import fetch
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import DictField, InstanceField, SubstitutionField
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
    yaql_query_values = Column(String(SMALL_STRING_LENGTH), default="")
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
        device: Optional[Device] = None,
        parent: Optional[Job] = None,
    ) -> dict:
        if self.origin_of_values == "user_provided_values":
            if device.name in self.user_provided_values:
                values = self.user_provided_values[device.name]
            else:
                values = self.user_provided_values["all"]
        else:
            query = self.sub(self.yaql_query_values, locals())
            values = factory.YaqlFactory().create()(query).evaluate(data=payload)
        if self.convert_values_to_devices:
            results, devices = {}, []
            for value in values:
                device = fetch("Device", **{self.conversion_property: value})
                if not device:
                    results[value] = "Error: no corresponding device"
                else:
                    devices.append(device)
            print("tttt"*100, devices)
            for device in devices:
                try:
                    result = self.iterated_job.job(payload, device, parent or self)
                except Exception as e:
                    result = str(e)
                results[device.name] = result
        else:
            results = {
                value: self.iterated_job.job(
                    {self.variable_name: value, **payload}, device
                )
                for value in values
            }
        return {"success": True, "Iteration values": values, **results}


class IterationForm(ServiceForm):
    form_type = HiddenField(default="IterationService")
    has_targets = BooleanField("Has Target Devices")
    origin_of_values = SelectField(
        "Where Values come from",
        choices=(
            ("user_provided_values", "User-provided Values (dictionary)"),
            ("yaql_query", "YaQL Query on the Payload"),
        ),
    )
    user_provided_values = DictField(
        "Iteration Values for Iteration: User provided "
        "(Expect dictionary {'all' : [...]} or {'device-name' : [...], ...})"
    )
    yaql_query_values = SubstitutionField(
        "Iteration Values for Iteration: YaQL query on the payload"
    )
    convert_values_to_devices = BooleanField("Convert values to devices")
    conversion_property = SelectField(
        "Property used for the conversion to devices",
        choices=(("name", "Name"), ("ip_address", "IP address")),
    )
    variable_name = StringField("Iteration Variable Name")
    iterated_job = InstanceField("Job to run for each Value", instance_type="Job")

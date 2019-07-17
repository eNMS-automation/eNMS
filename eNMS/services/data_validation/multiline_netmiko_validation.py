from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    PickleType,
    String,
    Text,
)
from sqlalchemy.ext.mutable import MutableDict
from typing import Optional
from wtforms import BooleanField, HiddenField

from eNMS.database import LARGE_STRING_LENGTH, SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.forms.services import NetmikoForm, ValidationForm
from eNMS.models.automation import Job, Service
from eNMS.models.inventory import Device


class MultilineNetmikoValidationService(Service):

    __tablename__ = "MultilineNetmikoValidationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    privileged_mode = Column(Boolean, default=False)
    commands = Column(Text(LARGE_STRING_LENGTH), default="")
    matches = Column(Text(LARGE_STRING_LENGTH), default="")
    driver = Column(String(SMALL_STRING_LENGTH), default="")
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=10.0)
    delay_factor = Column(Float, default=1.0)
    global_delay_factor = Column(Float, default=1.0)

    __mapper_args__ = {"polymorphic_identity": "MultilineNetmikoValidationService"}

    def job(self, payload: dict, device: Device, parent: Optional[Job] = None) -> dict:
        netmiko_connection = self.netmiko_connection(device, parent)
        commands = list(filter(None, self.sub(self.commands, locals()).splitlines()))
        matches = list(filter(None, self.sub(self.matches, locals()).splitlines()))
        results = {"success": True}
        for command, match in zip(commands, matches):

            result = self.convert_result(
                netmiko_connection.send_command(
                    command,
                    delay_factor=self.delay_factor,
                )
            )
            success = match in result
            results[command] = {"match": match, "result": result, "success": success}
            if not success:
                success = False
                break
        return {
            "match": match,
            "result": result,
            "success": True,
        }


class MultilineNetmikoValidationForm(ServiceForm, NetmikoForm):
    form_type = HiddenField(default="MultilineNetmikoValidationService")
    commands = SubstitutionField(widget=TextArea(), render_kw={"rows": 10})
    matches = SubstitutionField(widget=TextArea(), render_kw={"rows": 10})
    groups = {
        "Main Parameters": [

        ],
        "Netmiko Parameters": NetmikoForm.group,
    }

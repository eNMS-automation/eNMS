from io import StringIO
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from textfsm import TextFSM
from typing import Optional
from wtforms import (
    BooleanField,
    FloatField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
)
from wtforms.widgets import TextArea

from eNMS.controller import controller
from eNMS.database import LARGE_STRING_LENGTH, SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.models.automation import Job, Service
from eNMS.models.inventory import Device


class NetmikoTextfsmExtractionService(Service):

    __tablename__ = "NetmikoTextfsmExtractionService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    privileged_mode = Column(Boolean, default=False)
    command = Column(String(SMALL_STRING_LENGTH), default="")
    textfsm_template = Column(Text(LARGE_STRING_LENGTH), default="")
    driver = Column(String(SMALL_STRING_LENGTH), default="")
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=10.0)
    delay_factor = Column(Float, default=1.0)
    global_delay_factor = Column(Float, default=1.0)

    __mapper_args__ = {"polymorphic_identity": "NetmikoTextfsmExtractionService"}

    def job(self, payload: dict, device: Device, parent: Optional[Job] = None) -> dict:
        netmiko_handler = self.netmiko_connection(device)
        command = self.sub(self.command, locals())
        self.logs.append(f"Sending '{command}' on {device.name} (Netmiko)")
        output = netmiko_handler.send_command(command, delay_factor=self.delay_factor)
        textfsm_template = TextFSM(StringIO(self.textfsm_template))
        result = textfsm_template.ParseText(output)
        netmiko_handler.disconnect()
        return {"result": result, "output": output, "success": True}


class NetmikoTextfsmExtractionForm(ServiceForm):
    form_type = HiddenField(default="NetmikoTextfsmExtractionService")
    privileged_mode = BooleanField("Privileged mode (run in enable mode or as root)")
    command = StringField()
    textfsm_template = StringField(widget=TextArea(), render_kw={"rows": 5})
    driver = SelectField(choices=controller.NETMIKO_DRIVERS)
    use_device_driver = BooleanField(default=True)
    fast_cli = BooleanField()
    timeout = IntegerField(default=10)
    delay_factor = FloatField(default=1.0)
    global_delay_factor = FloatField(default=1.0)

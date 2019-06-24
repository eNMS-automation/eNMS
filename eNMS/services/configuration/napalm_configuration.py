from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String, Text
from sqlalchemy.ext.mutable import MutableDict
from typing import Optional
from wtforms import BooleanField, HiddenField, SelectField, StringField
from wtforms.widgets import TextArea

from eNMS.controller import controller
from eNMS.database import LARGE_STRING_LENGTH, SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import DictField
from eNMS.models.automation import Job, Service
from eNMS.models.inventory import Device


class NapalmConfigurationService(Service):

    __tablename__ = "NapalmConfigurationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    action = Column(String(SMALL_STRING_LENGTH), default="")
    content = Column(Text(LARGE_STRING_LENGTH), default="")
    driver = Column(String(SMALL_STRING_LENGTH), default="")
    use_device_driver = Column(Boolean, default=True)
    optional_args = Column(MutableDict.as_mutable(PickleType), default={})

    __mapper_args__ = {"polymorphic_identity": "NapalmConfigurationService"}

    def job(self, payload: dict, device: Device, parent: Optional[Job] = None) -> dict:
        napalm_driver = self.napalm_connection(device, parent)
        self.logs.append(f"Pushing configuration on {device.name} (Napalm)")
        config = "\n".join(self.sub(self.content, locals()).splitlines())
        getattr(napalm_driver, self.action)(config=config)
        napalm_driver.commit_config()
        if not parent:
            napalm_driver.close()
        return {"success": True, "result": f"Config push ({config})"}


class NapalmConfigurationForm(ServiceForm):
    form_type = HiddenField(default="NapalmConfigurationService")
    action = SelectField(
        choices=(
            ("load_merge_candidate", "Load merge"),
            ("load_replace_candidate", "Load replace"),
        )
    )
    content = StringField(widget=TextArea(), render_kw={"rows": 5})
    driver = SelectField(choices=controller.NAPALM_DRIVERS)
    use_device_driver = BooleanField(default=True)
    optional_args = DictField()

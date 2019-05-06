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
from wtforms import (
    BooleanField,
    FloatField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
)

from eNMS.controller import controller
from eNMS.database_helpers import LARGE_STRING_LENGTH, SMALL_STRING_LENGTH
from eNMS.forms import metaform
from eNMS.forms.automation import ServiceForm
from eNMS.forms.services import ValidationForm
from eNMS.models import metamodel
from eNMS.models.automation import Service
from eNMS.models.inventory import Device


class NetmikoValidationService(Service, metaclass=metamodel):

    __tablename__ = "NetmikoValidationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    command = Column(String(SMALL_STRING_LENGTH), default="")
    conversion_method = Column(String(SMALL_STRING_LENGTH), default="text")
    validation_method = Column(String(SMALL_STRING_LENGTH), default="text")
    content_match = Column(Text(LARGE_STRING_LENGTH), default="")
    content_match_regex = Column(Boolean, default=False)
    dict_match = Column(MutableDict.as_mutable(PickleType), default={})
    negative_logic = Column(Boolean, default=False)
    delete_spaces_before_matching = Column(Boolean, default=False)
    driver = Column(String(SMALL_STRING_LENGTH), default="")
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=10.0)
    delay_factor = Column(Float, default=1.0)
    global_delay_factor = Column(Float, default=1.0)

    __mapper_args__ = {"polymorphic_identity": "NetmikoValidationService"}

    def job(self, payload: dict, device: Device) -> dict:
        netmiko_handler = self.netmiko_connection(device)
        command = self.sub(self.command, locals())
        self.logs.append(f"Sending '{command}' on {device.name} (Netmiko)")
        result = netmiko_handler.send_command(command, delay_factor=self.delay_factor)
        match = self.sub(self.content_match, locals())
        netmiko_handler.disconnect()
        return {
            "match": match if self.validation_method == "text" else self.dict_match,
            "negative_logic": self.negative_logic,
            "result": result,
            "success": self.match_content(result, match),
        }


class NetmikoValidationForm(ServiceForm, ValidationForm, metaclass=metaform):
    form_type = HiddenField(default="NetmikoValidationService")
    command = StringField()
    conversion_method = SelectField(
        choices=(
            ("text", "Text"),
            ("json", "Json dictionary"),
            ("xml", "XML dictionary"),
        )
    )
    driver = SelectField(choices=controller.NETMIKO_DRIVERS)
    use_device_driver = BooleanField(default=True)
    fast_cli = BooleanField()
    timeout = IntegerField()
    delay_factor = FloatField()
    global_delay_factor = FloatField()

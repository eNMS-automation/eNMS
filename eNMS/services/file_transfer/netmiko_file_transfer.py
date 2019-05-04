from netmiko import file_transfer
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String
from wtforms import BooleanField, FloatField, IntegerField, SelectField, StringField
from wtforms.validators import InputRequired

from eNMS.forms import service_metaform
from eNMS.forms.automation import ServiceForm
from eNMS.controller import controller
from eNMS.models import register_class
from eNMS.models.automation import Service
from eNMS.models.inventory import Device


class NetmikoFileTransferService(Service, metaclass=register_class):

    __tablename__ = "NetmikoFileTransferService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    source_file = Column(String(255), default="")
    dest_file = Column(String(255), default="")
    direction = Column(String(255), default="")
    direction_values = (("put", "Upload"), ("get", "Download"))
    disable_md5 = Column(Boolean, default=False)
    driver = Column(String(255), default="")
    driver_values = controller.NETMIKO_SCP_DRIVERS
    use_device_driver = Column(Boolean, default=True)
    file_system = Column(String(255), default="")
    inline_transfer = Column(Boolean, default=False)
    overwrite_file = Column(Boolean, default=False)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=1)
    global_delay_factor = Column(Float, default=1.0)

    __mapper_args__ = {"polymorphic_identity": "NetmikoFileTransferService"}

    def job(self, payload: dict, device: Device) -> dict:
        netmiko_handler = self.netmiko_connection(device)
        self.logs.append("Transferring file {self.source_file} on {device.name}")
        transfer_dict = file_transfer(
            netmiko_handler,
            source_file=self.source_file,
            dest_file=self.dest_file,
            file_system=self.file_system,
            direction=self.direction,
            overwrite_file=self.overwrite_file,
            disable_md5=self.disable_md5,
            inline_transfer=self.inline_transfer,
        )
        netmiko_handler.disconnect()
        return {"success": True, "result": transfer_dict}


class NetmikoFileTransferForm(ServiceForm, metaclass=service_metaform):
    service_class = "NetmikoFileTransferService"
    source_file = StringField(validators=[InputRequired()])
    dest_file = StringField(validators=[InputRequired()])
    direction = SelectField(choices=(("put", "Upload"), ("get", "Download")))
    disable_md5 = BooleanField()
    driver = SelectField(choices=controller.NETMIKO_SCP_DRIVERS)
    use_device_driver = BooleanField()
    file_system = StringField()
    inline_transfer = BooleanField()
    overwrite_file = BooleanField()
    fast_cli = BooleanField()
    timeout = IntegerField(default=1)
    global_delay_factor = FloatField(default=1.0)

from netmiko import file_transfer
from sqlalchemy import Boolean, Float, ForeignKey, Integer
from wtforms import BooleanField, HiddenField, SelectField, StringField
from wtforms.validators import InputRequired

from eNMS.database.dialect import Column, SmallString
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.forms.services import NetmikoForm
from eNMS.models.automation import Run, Service
from eNMS.models.inventory import Device


class NetmikoFileTransferService(Service):

    __tablename__ = "NetmikoFileTransferService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    privileged_mode = Column(Boolean, default=False)
    source_file = Column(SmallString)
    destination_file = Column(SmallString)
    direction = Column(SmallString)
    disable_md5 = Column(Boolean, default=False)
    driver = Column(SmallString)
    use_device_driver = Column(Boolean, default=True)
    file_system = Column(SmallString)
    inline_transfer = Column(Boolean, default=False)
    overwrite_file = Column(Boolean, default=False)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=1)
    global_delay_factor = Column(Float, default=1.0)

    __mapper_args__ = {"polymorphic_identity": "NetmikoFileTransferService"}

    def job(self, run: "Run", payload: dict, device: Device) -> dict:
        netmiko_connection = run.netmiko_connection(device)
        source = run.sub(run.source_file, locals())
        destination = run.sub(run.destination_file, locals())
        run.log("info", f"Transferring file {source} on {device.name}")
        transfer_dict = file_transfer(
            netmiko_connection,
            source_file=source,
            dest_file=destination,
            file_system=run.file_system,
            direction=run.direction,
            overwrite_file=run.overwrite_file,
            disable_md5=run.disable_md5,
            inline_transfer=run.inline_transfer,
        )
        return {"success": True, "result": transfer_dict}


class NetmikoFileTransferForm(ServiceForm, NetmikoForm):
    form_type = HiddenField(default="NetmikoFileTransferService")
    source_file = SubstitutionField(validators=[InputRequired()])
    destination_file = SubstitutionField(validators=[InputRequired()])
    file_system = StringField()
    direction = SelectField(choices=(("put", "Upload"), ("get", "Download")))
    disable_md5 = BooleanField()
    inline_transfer = BooleanField()
    overwrite_file = BooleanField()
    groups = {
        "Main Parameters": [
            "source_file",
            "destination_file",
            "file_system",
            "direction",
            "disable_md5",
            "inline_transfer",
            "overwrite_file",
        ],
        "Netmiko Parameters": NetmikoForm.group,
    }

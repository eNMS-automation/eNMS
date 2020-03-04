from netmiko import file_transfer
from sqlalchemy import Boolean, Float, ForeignKey, Integer
from wtforms import BooleanField, HiddenField
from wtforms.validators import InputRequired

from eNMS.database.dialect import Column, SmallString
from eNMS.forms.fields import SelectField, StringField
from eNMS.forms.automation import NetmikoForm
from eNMS.models.automation import ConnectionService


class NetmikoFileTransferService(ConnectionService):

    __tablename__ = "netmiko_file_transfer_service"
    pretty_name = "Netmiko File Transfer"
    parent_type = "connection_service"
    id = Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    enable_mode = Column(Boolean, default=True)
    config_mode = Column(Boolean, default=False)
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

    __mapper_args__ = {"polymorphic_identity": "netmiko_file_transfer_service"}

    def job(self, run, payload, device):
        netmiko_connection = run.netmiko_connection(device)
        source = run.sub(run.source_file, locals())
        destination = run.sub(run.destination_file, locals())
        run.log("info", f"Transferring file {source}", device)
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


class NetmikoFileTransferForm(NetmikoForm):
    form_type = HiddenField(default="netmiko_file_transfer_service")
    source_file = StringField(validators=[InputRequired()], substitution=True)
    destination_file = StringField(validators=[InputRequired()], substitution=True)
    file_system = StringField()
    direction = SelectField(choices=(("put", "Upload"), ("get", "Download")))
    disable_md5 = BooleanField()
    inline_transfer = BooleanField()
    overwrite_file = BooleanField()
    groups = {
        "Main Parameters": {
            "commands": [
                "source_file",
                "destination_file",
                "file_system",
                "direction",
                "disable_md5",
                "inline_transfer",
                "overwrite_file",
            ],
            "default": "expanded",
        },
        **NetmikoForm.groups,
    }

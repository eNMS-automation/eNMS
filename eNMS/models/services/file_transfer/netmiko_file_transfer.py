from netmiko import file_transfer
from sqlalchemy import Boolean, Float, ForeignKey, Integer
from wtforms.validators import InputRequired

from eNMS.database import db
from eNMS.fields import BooleanField, HiddenField, SelectField, StringField
from eNMS.forms import NetmikoForm
from eNMS.models.automation import ConnectionService


class NetmikoFileTransferService(ConnectionService):
    __tablename__ = "netmiko_file_transfer_service"
    pretty_name = "Netmiko File Transfer"
    parent_type = "connection_service"
    id = db.Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    enable_mode = db.Column(Boolean, default=True)
    config_mode = db.Column(Boolean, default=False)
    source_file = db.Column(db.SmallString)
    destination_file = db.Column(db.SmallString)
    direction = db.Column(db.SmallString)
    disable_md5 = db.Column(Boolean, default=False)
    driver = db.Column(db.SmallString)
    file_system = db.Column(db.SmallString)
    inline_transfer = db.Column(Boolean, default=False)
    overwrite_file = db.Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "netmiko_file_transfer_service"}

    def job(self, run, device):
        netmiko_connection = run.netmiko_connection(device)
        source = run.sub(run.source_file, locals())
        destination = run.sub(run.destination_file, locals())
        run.log("info", f"Transferring file {source}", device)
        transfer_dict = file_transfer(
            netmiko_connection,
            source_file=source,
            dest_file=destination,
            file_system=run.file_system or None,
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

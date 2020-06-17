from glob import glob
from os.path import split
from pathlib import Path
from paramiko import SSHClient, AutoAddPolicy
from sqlalchemy import Boolean, Float, ForeignKey, Integer
from wtforms.validators import InputRequired

from eNMS import app
from eNMS.database import db
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import (
    BooleanField,
    FloatField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
)
from eNMS.models.automation import Service


class GenericFileTransferService(Service):

    __tablename__ = "generic_file_transfer_service"
    pretty_name = "Generic File Transfer"
    id = db.Column(Integer, ForeignKey("service.id"), primary_key=True)
    direction = db.Column(db.SmallString)
    protocol = db.Column(db.SmallString)
    source_file = db.Column(db.SmallString)
    destination_file = db.Column(db.SmallString)
    missing_host_key_policy = db.Column(Boolean, default=False)
    load_known_host_keys = db.Column(Boolean, default=False)
    look_for_keys = db.Column(Boolean, default=False)
    source_file_includes_globbing = db.Column(Boolean, default=False)
    max_transfer_size = db.Column(Integer, default=2 ** 30)
    window_size = db.Column(Integer, default=2 ** 30)
    timeout = db.Column(Float, default=10.0)

    __mapper_args__ = {"polymorphic_identity": "generic_file_transfer_service"}

    def job(self, run, payload, device):
        ssh_client = SSHClient()
        if run.missing_host_key_policy:
            ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        if run.load_known_host_keys:
            ssh_client.load_system_host_keys()
        source = run.sub(run.source_file, locals())
        destination = run.sub(run.destination_file, locals())
        success, result = True, f"File {source} transferred successfully"
        ssh_client.connect(
            device.ip_address,
            username=device.username,
            password=app.get_password(device.password),
            look_for_keys=run.look_for_keys,
        )
        if run.source_file_includes_globbing:
            glob_source_file_list = glob(source, recursive=False)
            if not glob_source_file_list:
                success = False
                result = f"Glob pattern {source} returned no matching files"
            else:
                pairs = []
                for glob_source in glob_source_file_list:
                    if Path(glob_source).is_dir():
                        run.log(
                            "warn",
                            (
                                f"Skipping glob transfer of directory"
                                f"{glob_source} to {destination}"
                            ),
                            device,
                        )
                        continue
                    _, filename = split(glob_source)
                    if destination[-1] != "/":
                        destination = destination + "/"
                    glob_destination = destination + filename
                    pairs.append((glob_source, glob_destination))
                run.log(
                    "info",
                    (
                        f"Transferring glob file(s)"
                        f"{glob_source_file_list} to {destination}"
                    ),
                    device,
                )
                run.transfer_file(ssh_client, pairs)
        elif not Path(source).is_file():
            success = False
            result = (
                f"Source file {source} does not exist, is a directory,"
                " or you forgot to enable globbing"
            )
        else:
            run.log("info", f"Transferring file {source} to {destination}", device)
            run.transfer_file(ssh_client, [(source, destination)])
        ssh_client.close()
        return {"success": success, "result": result}


class GenericFileTransferForm(ServiceForm):
    form_type = HiddenField(default="generic_file_transfer_service")
    direction = SelectField(choices=(("get", "Get"), ("put", "Put")))
    protocol = SelectField(choices=(("scp", "SCP"), ("sftp", "SFTP")))
    source_file = StringField(validators=[InputRequired()], substitution=True)
    destination_file = StringField(validators=[InputRequired()], substitution=True)
    missing_host_key_policy = BooleanField()
    load_known_host_keys = BooleanField()
    look_for_keys = BooleanField()
    source_file_includes_globbing = BooleanField(
        "Source file includes glob pattern (Put Direction only)"
    )
    max_transfer_size = IntegerField(default=2 ** 30)
    window_size = IntegerField(default=2 ** 30)
    timeout = FloatField(default=10.0)

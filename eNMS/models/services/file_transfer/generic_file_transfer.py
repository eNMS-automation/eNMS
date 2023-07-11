from glob import glob
from os.path import split
from pathlib import Path
from paramiko import SSHClient, AutoAddPolicy
from sqlalchemy import Boolean, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship
from wtforms.validators import InputRequired

from eNMS.database import db
from eNMS.forms import ServiceForm
from eNMS.fields import (
    BooleanField,
    FloatField,
    HiddenField,
    InstanceField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
)
from eNMS.models.automation import Service
from eNMS.variables import vs


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
    source_file_includes_globbing = db.Column(Boolean, default=False)
    max_transfer_size = db.Column(Integer, default=2**30)
    window_size = db.Column(Integer, default=2**30)
    timeout = db.Column(Float, default=10.0)
    credentials = db.Column(db.SmallString, default="device")
    named_credential_id = db.Column(Integer, ForeignKey("credential.id"))
    named_credential = relationship("Credential")
    custom_username = db.Column(db.SmallString)
    custom_password = db.Column(db.SmallString)

    __mapper_args__ = {"polymorphic_identity": "generic_file_transfer_service"}

    def job(self, run, device):
        ssh_client = SSHClient()
        if run.missing_host_key_policy:
            ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        if run.load_known_host_keys:
            ssh_client.load_system_host_keys()
        source = run.sub(run.source_file, locals())
        destination = run.sub(run.destination_file, locals())
        if run.direction == "put" and str(vs.file_path) not in source:
            source = f"{vs.file_path}{source}"
        if run.direction == "get" and str(vs.file_path) not in destination:
            destination = f"{vs.file_path}{destination}"
        credentials = run.get_credentials(device, add_secret=False)
        ssh_client.connect(device.ip_address, look_for_keys=False, **credentials)
        if run.source_file_includes_globbing:
            glob_source_file_list = glob(source, recursive=False)
            if not glob_source_file_list:
                return {
                    "success": False,
                    "result": f"Glob pattern {source} returned no matching files",
                }
            else:
                files = []
                for glob_source in glob_source_file_list:
                    if Path(glob_source).is_dir():
                        continue
                    _, filename = split(glob_source)
                    if destination[-1] != "/":
                        destination = destination + "/"
                    glob_destination = destination + filename
                    files.append((glob_source, glob_destination))
        else:
            files = [(source, destination)]
        log = ", ".join("Transferring {} to {}".format(*pairs) for pairs in files)
        run.log("info", log, device)
        run.transfer_file(ssh_client, files)
        ssh_client.close()
        return {"success": True, "result": "Transfer successful"}


class GenericFileTransferForm(ServiceForm):
    form_type = HiddenField(default="generic_file_transfer_service")
    direction = SelectField(choices=(("get", "Get"), ("put", "Put")))
    protocol = SelectField(choices=(("scp", "SCP"), ("sftp", "SFTP")))
    source_file = StringField(validators=[InputRequired()], substitution=True)
    destination_file = StringField(validators=[InputRequired()], substitution=True)
    missing_host_key_policy = BooleanField()
    load_known_host_keys = BooleanField()
    source_file_includes_globbing = BooleanField("Source file includes glob pattern")
    max_transfer_size = IntegerField(default=2**30)
    window_size = IntegerField(default=2**30)
    timeout = FloatField(default=10.0)
    credentials = SelectField(
        "Credentials",
        choices=(
            ("device", "Device Credentials"),
            ("object", "Named Credential"),
            ("custom", "Custom Credentials"),
        ),
    )
    named_credential = InstanceField("Named Credential", model="credential")
    custom_username = StringField("Custom Username", substitution=True)
    custom_password = PasswordField("Custom Password", substitution=True)

    def validate(self, **_):
        valid_form = super().validate()
        invalid_direction = (
            self.source_file_includes_globbing.data and self.direction.data == "get"
        )
        if invalid_direction:
            self.direction.errors.append("Globbing only works with the 'PUT' direction")
        return valid_form and not invalid_direction

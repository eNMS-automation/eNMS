from glob import glob
from logging import info
from os.path import split
from paramiko import SSHClient, AutoAddPolicy
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from typing import Optional
from wtforms import BooleanField, HiddenField, SelectField
from wtforms.validators import InputRequired

from eNMS.database import SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.models.automation import Job, Service
from eNMS.models.inventory import Device


class GenericFileTransferService(Service):

    __tablename__ = "GenericFileTransferService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    direction = Column(String(SMALL_STRING_LENGTH), default="")
    protocol = Column(String(SMALL_STRING_LENGTH), default="")
    source_file = Column(String(SMALL_STRING_LENGTH), default="")
    destination_file = Column(String(SMALL_STRING_LENGTH), default="")
    missing_host_key_policy = Column(Boolean, default=False)
    load_known_host_keys = Column(Boolean, default=False)
    look_for_keys = Column(Boolean, default=False)
    source_file_includes_globbing = Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "GenericFileTransferService"}

    def job(
        self, payload: dict, device: Device, parent: Optional[Job] = None
    ) -> dict:
        ssh_client = SSHClient()
        if self.missing_host_key_policy:
            ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        if self.load_known_host_keys:
            ssh_client.load_system_host_keys()
        source = self.sub(self.source_file, locals())
        destination = self.sub(self.destination_file, locals())
        self.logger("Transferring file {source} on {device.name}")
        success, result = True, f"File {source} transferred successfully"
        ssh_client.connect(
            device.ip_address,
            username=device.username,
            password=device.password,
            look_for_keys=self.look_for_keys,
        )

        if self.source_file_includes_globbing:
            glob_source_file_list = glob(source, recursive=False)
            if not glob_source_file_list:
                success = False
                result = f"Glob pattern {source} returned no matching files"
            else:
                pairs = []
                for glob_source in glob_source_file_list:
                    path, filename = split(glob_source)
                    if destination[-1] != "/":
                        destination = destination + "/"
                    glob_destination = destination + filename
                    pairs.append((glob_source, glob_destination))
                info(f"Preparing to transfer glob file {glob_source}")
                self.transfer_file(ssh_client, pairs)
        else:
            self.transfer_file(ssh_client, source, destination)
        ssh_client.close()
        return {"success": success, "result": result}


class GenericFileTransferForm(ServiceForm):
    form_type = HiddenField(default="GenericFileTransferService")
    direction = SelectField(choices=(("get", "Get"), ("put", "Put")))
    protocol = SelectField(choices=(("scp", "SCP"), ("sftp", "SFTP")))
    source_file = SubstitutionField(validators=[InputRequired()])
    destination_file = SubstitutionField(validators=[InputRequired()])
    missing_host_key_policy = BooleanField()
    load_known_host_keys = BooleanField()
    look_for_keys = BooleanField()
    source_file_includes_globbing = BooleanField(
        "Source file includes glob pattern (Put Direction only)"
    )

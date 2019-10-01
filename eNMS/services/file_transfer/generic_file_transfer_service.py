from glob import glob
from logging import info
from os.path import split
from paramiko import SSHClient, AutoAddPolicy
from sqlalchemy import Boolean, ForeignKey, Integer
from wtforms import BooleanField, HiddenField, IntegerField, SelectField
from wtforms.validators import InputRequired

from eNMS.database.dialect import Column, SmallString
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.models.automation import Service


class GenericFileTransferService(Service):

    __tablename__ = "generic_file_transfer_service"
    pretty_name = "Generic File Transfer"

    id = Column(Integer, ForeignKey("service.id"), primary_key=True)
    direction = Column(SmallString)
    protocol = Column(SmallString)
    source_file = Column(SmallString)
    destination_file = Column(SmallString)
    missing_host_key_policy = Column(Boolean, default=False)
    load_known_host_keys = Column(Boolean, default=False)
    look_for_keys = Column(Boolean, default=False)
    source_file_includes_globbing = Column(Boolean, default=False)
    max_transfer_size = Column(Integer, default=2 ** 30)
    window_size = Column(Integer, default=2 ** 30)

    __mapper_args__ = {"polymorphic_identity": "generic_file_transfer_service"}

    def job(self, run, payload, device):
        ssh_client = SSHClient()
        if run.missing_host_key_policy:
            ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        if run.load_known_host_keys:
            ssh_client.load_system_host_keys()
        source = run.sub(run.source_file, locals())
        destination = run.sub(run.destination_file, locals())
        run.log("info", "Transferring file {source} on {device.name}")
        success, result = True, f"File {source} transferred successfully"
        ssh_client.connect(
            device.ip_address,
            username=device.username,
            password=device.password,
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
                    path, filename = split(glob_source)
                    if destination[-1] != "/":
                        destination = destination + "/"
                    glob_destination = destination + filename
                    pairs.append((glob_source, glob_destination))
                info(f"Preparing to transfer glob file {glob_source}")
                run.transfer_file(ssh_client, pairs)
        else:
            run.transfer_file(ssh_client, [(source, destination)])
        ssh_client.close()
        return {"success": success, "result": result}


class GenericFileTransferForm(ServiceForm):
    form_type = HiddenField(default="generic_file_transfer_service")
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
    max_transfer_size = IntegerField(default=2 ** 30)
    window_size = IntegerField(default=2 ** 30)

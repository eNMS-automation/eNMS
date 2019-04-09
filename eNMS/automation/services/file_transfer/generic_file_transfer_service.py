from glob import glob
from os.path import split
from paramiko import SSHClient, AutoAddPolicy
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from logging import info

from eNMS.automation.models import Service
from eNMS.classes import service_classes
from eNMS.inventory.models import Device


class GenericFileTransferService(Service):

    __tablename__ = "GenericFileTransferService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    direction = Column(String(255))
    direction_values = (("get", "Get"), ("put", "Put"))
    protocol = Column(String(255))
    protocol_values = (("scp", "SCP"), ("sftp", "SFTP"))
    source_file = Column(String(255))
    destination_file = Column(String(255))
    missing_host_key_policy = Column(Boolean)
    load_known_host_keys = Column(Boolean)
    look_for_keys = Column(Boolean)
    source_file_includes_globbing = Column(Boolean)
    source_file_includes_globbing_name = (
        "Source file includes glob pattern (Put Direction only)"
    )

    __mapper_args__ = {"polymorphic_identity": "GenericFileTransferService"}

    def job(self, payload: dict, device: Device) -> dict:
        ssh_client = SSHClient()
        if self.missing_host_key_policy:
            ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        if self.load_known_host_keys:
            ssh_client.load_system_host_keys()
        source_file = self.sub(self.source_file, locals())
        self.logs.append("Transferring file {source_file} on {device.name}")
        success, result = True, f"File {source_file} transferred successfully"
        ssh_client.connect(
            device.ip_address,
            username=device.username,
            password=device.password,
            look_for_keys=self.look_for_keys,
        )
        source = self.sub(self.source_file, locals())
        destination = self.sub(self.destination_file, locals())
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
            self.transfer_file(
                ssh_client,
                self.sub(self.source_file, locals()),
                self.sub(self.destination_file, locals()),
            )
        ssh_client.close()
        return {"success": success, "result": result}


service_classes["GenericFileTransferService"] = GenericFileTransferService

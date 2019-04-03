from paramiko import SSHClient, AutoAddPolicy
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
import glob
import os
from traceback import format_exc
from logging import info

from eNMS.automation.models import Service
from eNMS.base.classes import service_classes
from eNMS.inventory.models import Device


class GenericFileTransferService(Service):

    __tablename__ = "GenericFileTransferService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    direction = Column(String)
    direction_values = (("get", "Get"), ("put", "Put"))
    protocol = Column(String)
    protocol_values = (("scp", "SCP"), ("sftp", "SFTP"))
    source_file = Column(String)
    destination_file = Column(String)
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
        success, result = True, f"File {source_file} transferred successfully"
        try:
            ssh_client.connect(
                device.ip_address,
                username=device.username,
                password=device.password,
                look_for_keys=self.look_for_keys,
            )
        except Exception as e:
            success = False
            result = f"Connection to {device.ip_address} failed: {chr(10).join(format_exc().splitlines())}"

        substituted_source = self.sub(self.source_file, locals())
        substituted_destination = self.sub(self.destination_file, locals())

        if self.source_file_includes_globbing:
            glob_source_file_list = glob.glob(substituted_source, recursive=False)
            if not glob_source_file_list:
                success = False
                result = f"Glob pattern {substituted_source} returned no matching files"
            else:
                source_destination_pairs_list = []
                for glob_source in glob_source_file_list:
                    path, filename = os.path.split(glob_source)
                    if substituted_destination[-1] != "/":
                        substituted_destination = substituted_destination + "/"
                    glob_destination = substituted_destination + filename
                    source_destination_pairs_list.append(
                        (glob_source, glob_destination)
                    )
                info(f"Preparing to transfer glob file {glob_source}")
                try:
                    self.transfer_file(ssh_client, source_destination_pairs_list)

                except Exception as e:
                    success = False
                    result = f"Transferring the file list {source_destination_pairs_list} failed,\nremember to only give destination directory when provising a glob pattern:\n{chr(10).join(format_exc().splitlines())}"
        else:
            try:
                self.transfer_file(
                    ssh_client,
                    self.sub(self.source_file, locals()),
                    self.sub(self.destination_file, locals()),
                )
            except Exception as e:
                success = False
                result = f"Transferring the file {substituted_source} to {substituted_destination} failed:\n{chr(10).join(format_exc().splitlines())}"
        ssh_client.close()
        return {"success": success, "result": result}


service_classes["GenericFileTransferService"] = GenericFileTransferService

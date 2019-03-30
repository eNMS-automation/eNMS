from paramiko import SSHClient, AutoAddPolicy
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

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
            result = f"Connection to {device.ip_address} failed ({str(e)})"
        try:
            self.transfer_file(
                ssh_client,
                self.sub(self.source_file, locals()),
                self.sub(self.destination_file, locals()),
            )
        except Exception as e:
            success = False
            result = f"Transferring the file {source_file} failed({str(e)})"
        ssh_client.close()
        return {"success": success, "result": result}


service_classes["GenericFileTransferService"] = GenericFileTransferService

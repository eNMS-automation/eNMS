from datetime import datetime
from paramiko import SSHClient, AutoAddPolicy
from pathlib import Path
from os import remove
from shutil import rmtree
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from tarfile import open as open_tar

from eNMS.admin.functions import migrate_export
from eNMS.automation.models import Service
from eNMS.classes import service_classes
from eNMS.functions import strip_all
from eNMS.properties import import_properties
from eNMS.inventory.models import Device


class DatabaseBackupService(Service):

    __tablename__ = "DatabaseBackupService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    direction = "put"
    protocol = Column(String(255))
    protocol_values = (("scp", "SCP"), ("sftp", "SFTP"))
    delete_folder = Column(Boolean)
    delete_archive = Column(Boolean)
    destination_path = Column(String(255))

    __mapper_args__ = {"polymorphic_identity": "DatabaseBackupService"}

    def job(self, payload: dict, device: Device) -> dict:
        now = strip_all(str(datetime.now()))
        source = Path.cwd() / "migrations" / f"backup_{now}.tgz"
        migrate_export(
            Path.cwd(),
            {"import_export_types": list(import_properties), "name": f"backup_{now}"},
        )
        with open_tar(source, "w:gz") as tar:
            tar.add(Path.cwd() / "migrations" / f"backup_{now}", arcname="/")
        ssh_client = SSHClient()
        ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        ssh_client.connect(
            device.ip_address,
            username=device.username,
            password=device.password,
            look_for_keys=False,
        )
        destination = f"{self.destination_path}/backup_{now}.tgz"
        self.transfer_file(ssh_client, [(source, destination)])
        ssh_client.close()
        if self.delete_folder:
            rmtree(Path.cwd() / "migrations" / f"backup_{now}")
        if self.delete_archive:
            remove(source)
        return {
            "success": True,
            "result": f"backup stored in {destination} ({device.ip_address})",
        }


service_classes["DatabaseBackupService"] = DatabaseBackupService

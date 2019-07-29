from paramiko import SSHClient, AutoAddPolicy
from pathlib import Path
from os import remove
from shutil import rmtree
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from tarfile import open as open_tar
from typing import Optional
from wtforms import BooleanField, HiddenField, SelectField

from eNMS.controller import controller
from eNMS.database import SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.models.automation import Job, Service
from eNMS.models.inventory import Device
from eNMS.properties.database import import_classes


class DatabaseBackupService(Service):

    __tablename__ = "DatabaseBackupService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    direction = "put"
    protocol = Column(String(SMALL_STRING_LENGTH), default="")
    delete_folder = Column(Boolean, default=False)
    delete_archive = Column(Boolean, default=False)
    destination_path = Column(String(SMALL_STRING_LENGTH), default="")

    __mapper_args__ = {"polymorphic_identity": "DatabaseBackupService"}

    def job(self, run: "Run", payload: dict, device: Device) -> dict:
        now = controller.strip_all(controller.get_time())
        source = Path.cwd() / "projects" / "migrations" / f"backup_{now}.tgz"
        controller.migrate_export(
            Path.cwd(), {"import_export_types": import_classes, "name": f"backup_{now}"}
        )
        with open_tar(source, "w:gz") as tar:
            tar.add(
                Path.cwd() / "projects" / "migrations" / f"backup_{now}", arcname="/"
            )
        ssh_client = SSHClient()
        ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        ssh_client.connect(
            device.ip_address,
            username=device.username,
            password=device.password,
            look_for_keys=False,
        )
        destination = f"{self.sub(self.destination_path, locals())}/backup_{now}.tgz"
        run.transfer_file(ssh_client, [(source, destination)])
        ssh_client.close()
        if self.delete_folder:
            rmtree(Path.cwd() / "projects" / "migrations" / f"backup_{now}")
        if self.delete_archive:
            remove(source)
        return {
            "success": True,
            "result": f"backup stored in {destination} ({device.ip_address})",
        }


class DatabaseBackupForm(ServiceForm):
    form_type = HiddenField(default="DatabaseBackupService")
    protocol = SelectField(choices=(("scp", "SCP"), ("sftp", "SFTP")))
    delete_folder = BooleanField()
    delete_archive = BooleanField()
    destination_path = SubstitutionField()

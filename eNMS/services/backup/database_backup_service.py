from paramiko import SSHClient, AutoAddPolicy
from pathlib import Path
from os import remove
from shutil import rmtree
from sqlalchemy import Boolean, ForeignKey, Integer
from tarfile import open as open_tar
from wtforms import BooleanField, HiddenField, SelectField

from eNMS import app
from eNMS.database.dialect import Column, SmallString
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.models.automation import Service
from eNMS.models.execution import Run
from eNMS.models.inventory import Device
from eNMS.properties.database import import_classes


class DatabaseBackupService(Service):

    __tablename__ = "DatabaseBackupService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    direction = "put"
    protocol = Column(SmallString)
    delete_folder = Column(Boolean, default=False)
    delete_archive = Column(Boolean, default=False)
    destination_path = Column(SmallString)

    __mapper_args__ = {"polymorphic_identity": "DatabaseBackupService"}

    def job(self, run: "Run", payload: dict, device: Device) -> dict:
        now = app.strip_all(app.get_time())
        source = Path.cwd() / "projects" / "migrations" / f"backup_{now}.tgz"
        app.migrate_export(
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
        destination = f"{run.sub(run.destination_path, locals())}/backup_{now}.tgz"
        run.transfer_file(ssh_client, [(source, destination)])
        ssh_client.close()
        if run.delete_folder:
            rmtree(Path.cwd() / "projects" / "migrations" / f"backup_{now}")
        if run.delete_archive:
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

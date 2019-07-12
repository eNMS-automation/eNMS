from paramiko import SSHClient, AutoAddPolicy
from pathlib import Path
from os import makedirs, remove
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


class LogBackupService(Service):

    __tablename__ = "LogBackupService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    direction = "put"
    protocol = Column(String(SMALL_STRING_LENGTH), default="")
    delete_folder = Column(Boolean, default=False)
    delete_archive = Column(Boolean, default=False)
    destination_path = Column(String(SMALL_STRING_LENGTH), default="")

    __mapper_args__ = {"polymorphic_identity": "LogBackupService"}

    def job(self, payload: dict, device: Device, parent: Optional[Job] = None) -> dict:
        path_backup = Path.cwd() / "logs" / "job_logs"
        now = controller.strip_all(controller.get_time())
        path_dir = path_backup / f"logs_{now}"
        source = path_backup / f"logs_{now}.tgz"
        makedirs(path_dir)
        # TODO TO REIMPLEMENT LOG BACKUP
        """ for job in fetch_all("Job"):
            with open(path_dir / f"{job.name}.json", "w") as log_file:
                dump(logs, log_file) """
        with open_tar(source, "w:gz") as tar:
            tar.add(path_dir, arcname="/")
        ssh_client = SSHClient()
        ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        ssh_client.connect(
            device.ip_address,
            username=device.username,
            password=device.password,
            look_for_keys=False,
        )
        destination = f"{self.sub(self.destination_path, locals())}/logs_{now}.tgz"
        self.transfer_file(ssh_client, [(source, destination)])
        ssh_client.close()
        if self.delete_folder:
            rmtree(path_dir)
        if self.delete_archive:
            remove(source)
        return {
            "success": True,
            "result": f"logs stored in {destination} ({device.ip_address})",
        }


class LogBackupForm(ServiceForm):
    form_type = HiddenField(default="LogBackupService")
    protocol = SelectField(choices=(("scp", "SCP"), ("sftp", "SFTP")))
    delete_folder = BooleanField()
    delete_archive = BooleanField()
    destination_path = SubstitutionField()

from json import dump
from paramiko import SSHClient, AutoAddPolicy
from pathlib import Path
from os import makedirs, remove
from shutil import rmtree
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from tarfile import open as open_tar
from wtforms import BooleanField, HiddenField, SelectField, StringField

from eNMS.controller import controller
from eNMS.database import fetch_all
from eNMS.forms import metaform
from eNMS.forms.automation import ServiceForm
from eNMS.models import register_class
from eNMS.models.automation import Service
from eNMS.models.inventory import Device


class LogBackupService(Service, metaclass=register_class):

    __tablename__ = "LogBackupService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    direction = "put"
    protocol = Column(String(255), default="")
    delete_folder = Column(Boolean, default=False)
    delete_archive = Column(Boolean, default=False)
    destination_path = Column(String(255), default="")

    __mapper_args__ = {"polymorphic_identity": "LogBackupService"}

    def job(self, payload: dict, device: Device) -> dict:
        path_backup = Path.cwd() / "logs" / "job_logs"
        now = controller.strip_all(controller.get_time())
        path_dir = path_backup / f"logs_{now}"
        source = path_backup / f"logs_{now}.tgz"
        makedirs(path_dir)
        for job in fetch_all("Job"):
            with open(path_dir / f"{job.name}.json", "w") as log_file:
                dump(job.logs, log_file)
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
        destination = f"{self.destination_path}/logs_{now}.tgz"
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


class LogBackupForm(ServiceForm, metaclass=metaform):
    form_type = HiddenField(default="LogBackupService")
    protocol = SelectField(choices=(("scp", "SCP"), ("sftp", "SFTP")))
    delete_folder = BooleanField()
    delete_archive = BooleanField()
    destination_path = StringField()

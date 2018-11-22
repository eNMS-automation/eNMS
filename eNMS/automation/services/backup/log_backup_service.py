from datetime import datetime
from json import dump
from paramiko import SSHClient, AutoAddPolicy
from pathlib import Path
from os import makedirs
from shutil import rmtree
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from tarfile import open as open_tar

from eNMS.automation.models import Service
from eNMS.base.classes import service_classes
from eNMS.base.helpers import fetch_all, strip_all


class LogBackupService(Service):

    __tablename__ = 'LogBackupService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = True
    direction = 'put'
    protocol = Column(String)
    protocol_values = (('scp', 'SCP'), ('sftp', 'SFTP'))
    delete_directory_and_archive = Column(Boolean)
    destination_path = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'LogBackupService',
    }

    def job(self, device, _):
        path_backup = Path.cwd() / 'logs' / 'job_logs'
        now = strip_all(str(datetime.now()))
        path_dir = path_backup / f'logs_{now}'
        makedirs(path_dir)
        for job in fetch_all('Job'):
            with open(path_dir / f'{job.name}.json', 'w') as log_file:
                dump(job.logs, log_file)
        with open_tar(f'logs_{now}', 'w:gz') as tar:
            tar.add(path_dir)
        ssh_client = SSHClient()
        ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        ssh_client.connect(
            device.ip_address,
            username=device.username,
            password=device.password,
            look_for_keys=False
        )
        self.transfer_file(
            ssh_client,
            path_backup / f'logs_{now}',
            self.destination_path / f'logs_{now}'
        )
        ssh_client.close()
        if self.delete_directory_and_archive:
            rmtree(path_dir)
            #TODO delete archive
        return {
            'success': True,
            'result': path_backup
        }


service_classes['LogBackupService'] = LogBackupService

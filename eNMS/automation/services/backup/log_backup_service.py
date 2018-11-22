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
from eNMS.base.helpers import fetch_all


class LogBackupService(Service):

    __tablename__ = 'LogBackupService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = False
    protocol = Column(String)
    protocol_values = (('scp', 'SCP'), ('sftp', 'SFTP'))
    delete_directory_and_archive = Column(Boolean)
    server_ip_address = Column(String)
    destination_path = Column(String)
    username = Column(String)
    password = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'LogBackupService',
    }

    def job(self, _):
        path_backup = Path.cwd() / 'logs' / 'job_logs'
        now = str(datetime.now()).replace(' ', '-')
        path_dir = path_backup / f'logs_{now}'
        makedirs(path_dir)
        for job in fetch_all('Job'):
            with open(path_dir / f'{job.name}.json', 'w') as log_file:
                dump(job.logs, log_file)
        with open_tar(f'logs_{now}', 'w:gz') as tar:
            tar.add('json')
        ssh_client = SSHClient()
        ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        ssh_client.connect(
            self.server_ip_address,
            username=self.username,
            password=self.password,
            look_for_keys=False
        )
        self.transfer_file(ssh_client)
        ssh_client.close()
        rmtree(path_dir)
        return {
            'success': True,
            'result': path_backup
        }


service_classes['LogBackupService'] = LogBackupService

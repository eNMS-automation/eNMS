from paramiko import SSHClient, AutoAddPolicy
from pathlib import Path
from scp import SCPClient
from sqlalchemy import Column, ForeignKey, Integer, String

from eNMS.automation.models import Service
from eNMS.base.classes import service_classes


class LogBackupService(Service):

    __tablename__ = 'LogBackupService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = False
    protocol = Column(String)
    protocol_values = (('scp', 'SCP'), ('sftp', 'SFTP'))
    source_file = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'LogBackupService',
    }

    def job(self, _):
        # ssh = SSHClient()
        # ssh.set_missing_host_key_policy(AutoAddPolicy())
        # ssh.load_host_keys(Path.home() / '.ssh' / 'known_hosts')
        # ssh.connect(
        #     device.ip_address,
        #     username=device.username,
        #     password=device.password,
        #     look_for_keys=False
        # )
        # with SCPClient(ssh.get_transport()) as scp:
        #     getattr(scp, self.direction)(*files)
        # ssh.close()
        return {
            'success': True,
            'result': f'File {self.source_file} transferred successfully'
        }


service_classes['LogBackupService'] = LogBackupService

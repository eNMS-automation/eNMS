from paramiko import SSHClient, AutoAddPolicy
from pathlib import Path
from scp import SCPClient
from sqlalchemy import Column, ForeignKey, Integer, String

from eNMS.automation.models import Service
from eNMS.base.classes import service_classes


class GenericFileTransferService(Service):

    __tablename__ = 'GenericFileTransferService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = True
    direction = Column(String)
    direction_values = (('get', 'Get'), ('put', 'Put'))
    protocol = Column(String)
    protocol_values = (('scp', 'SCP'), ('sftp', 'SFTP'))
    source_file = Column(String)
    destination_file = Column(String)
    missing_host_key_policy = Column(Boolean)
    load_known_host_keys = Column(Boolean)
    look_for_keys = Column(Boolean)

    __mapper_args__ = {
        'polymorphic_identity': 'GenericFileTransferService',
    }

    def job(self, device, _):
        ssh = SSHClient()
        if self.missing_host_key_policy:
            ssh.set_missing_host_key_policy(AutoAddPolicy())
        if self.load_known_host_keys:
            ssh.load_system_host_keys()
        ssh.connect(
            device.ip_address,
            username=device.username,
            password=device.password,
            look_for_keys=self.look_for_keys
        )
        files = (self.source_file, self.destination_file)
        if self.protocol == 'sftp':
            sftp = ssh.open_sftp()
            getattr(sftp, self.direction)(*files)
            sftp.close()
        else:
            with SCPClient(ssh.get_transport()) as scp:
                getattr(scp, self.direction)(*files)
        ssh.close()
        return {
            'success': True,
            'result': f'File {self.source_file} transferred successfully'
        }


service_classes['GenericFileTransferService'] = GenericFileTransferService

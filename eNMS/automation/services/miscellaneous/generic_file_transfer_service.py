from sqlalchemy import Column, ForeignKey, Integer, String

from eNMS.automation.models import Service
from eNMS.base.classes import service_classes

from os.path import expanduser
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient


class GenericFileTransferService(Service):

    __tablename__ = 'GenericFileTransferService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    direction = Column(String)
    direction_values = (('get', 'Get'), ('put', 'Put'))
    protocol = Column(String)
    protocol_values = (('scp', 'SCP'), ('sftp', 'SFTP'))
    source_file = Column(String)
    destination_file = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'GenericFileTransferService',
    }

    def job(self, device, payload):
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.load_host_keys(expanduser('~' / '.ssh' / 'known_hosts'))
        ssh.connect(
            device.ip_address,
            username=device.username,
            password=device.password,
            look_for_keys=False
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

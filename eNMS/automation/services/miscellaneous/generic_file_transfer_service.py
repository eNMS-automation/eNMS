from paramiko import SSHClient, AutoAddPolicy
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

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
        ssh_client = SSHClient()
        if self.missing_host_key_policy:
            ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        if self.load_known_host_keys:
            ssh_client.load_system_host_keys()
        ssh_client.connect(
            device.ip_address,
            username=device.username,
            password=device.password,
            look_for_keys=self.look_for_keys
        )
        self.transfer_file(
            ssh_client,
            self.sub(self.source_file, locals()),
            self.sub(self.destination_file, locals())
        )
        ssh_client.close()
        return {
            'success': True,
            'result': f'File {self.source_file} transferred successfully'
        }


service_classes['GenericFileTransferService'] = GenericFileTransferService

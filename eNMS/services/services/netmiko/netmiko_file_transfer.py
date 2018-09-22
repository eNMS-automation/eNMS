from multiprocessing.pool import ThreadPool
from netmiko import file_transfer
from netmiko.ssh_dispatcher import CLASS_MAPPER
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from eNMS.services.helpers import netmiko_connection
from eNMS.services.models import Service, service_classes


class NetmikoFileTransferService(Service):

    __tablename__ = 'NetmikoFileTransferService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    vendor = Column(String)
    operating_system = Column(String)
    driver = Column(String)
    source_file = Column(String)
    dest_file = Column(String)
    file_system = Column(String)
    direction = Column(String)
    overwrite_file = Column(Boolean)
    disable_md5 = Column(Boolean)
    inline_transfer = Column(Boolean)
    driver_values = (
        ('cisco_ios', 'Cisco IOS'),
        ('cisco_xe', 'Cisco IOS-XE'),
        ('cisco_xr', 'Cisco IOS-XR'),
        ('cisco_nxos', 'Cisco NX-OS'),
        ('juniper_junos', 'Juniper'),
        ('arista_eos', 'Arista')
    )
    direction_values = (('put', 'Upload'), ('get', 'Download'))

    __mapper_args__ = {
        'polymorphic_identity': 'netmiko_file_transfer_service',
    }

    def job(self, incoming_payload):
        device, results = args
        try:
            netmiko_handler = netmiko_connection(self, device)
            transfer_dict = file_transfer(
                netmiko_handler,
                source_file=self.source_file,
                dest_file=self.dest_file,
                file_system=self.file_system,
                direction=self.direction,
                overwrite_file=self.overwrite_file,
                disable_md5=self.disable_md5,
                inline_transfer=self.inline_transfer
            )
            result, success = transfer_dict, True
            netmiko_handler.disconnect()
        except Exception as e:
            result, success = f'task failed ({e})', False
            results['success'] = False
        results[device.name] = {'success': success, 'result': result}


service_classes['Netmiko File Transfer Service'] = NetmikoFileTransferService

from netmiko import file_transfer
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String

from eNMS.automation.helpers import NETMIKO_SCP_DRIVERS
from eNMS.automation.models import Service
from eNMS.base.classes import service_classes


class NetmikoFileTransferService(Service):

    __tablename__ = 'NetmikoFileTransferService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = True
    dest_file = Column(String)
    direction = Column(String)
    direction_values = (('put', 'Upload'), ('get', 'Download'))
    disable_md5 = Column(Boolean)
    driver = Column(String)
    driver_values = NETMIKO_SCP_DRIVERS
    use_device_driver = Column(Boolean, default=True)
    file_system = Column(String)
    inline_transfer = Column(Boolean)
    overwrite_file = Column(Boolean)
    source_file = Column(String)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=1.)
    global_delay_factor = Column(Float, default=1.)

    __mapper_args__ = {
        'polymorphic_identity': 'NetmikoFileTransferService',
    }

    def job(self, device, _):
        netmiko_handler = self.netmiko_connection(device)
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
        netmiko_handler.disconnect()
        return {'success': True, 'result': transfer_dict}


service_classes['NetmikoFileTransferService'] = NetmikoFileTransferService

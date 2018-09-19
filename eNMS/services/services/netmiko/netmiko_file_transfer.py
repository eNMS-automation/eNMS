from netmiko.ssh_dispatcher import CLASS_MAPPER
from sqlalchemy import Column, Float, ForeignKey, Integer, String

from eNMS.services.custom_service import CustomService, service_classes
from eNMS.services.models import multiprocessing

netmiko_drivers = sorted(
    driver for driver in CLASS_MAPPER
    if 'telnet' not in driver and 'ssh' not in driver
)


class NetmikoFileTransferService(CustomService):

    __tablename__ = 'NetmikoFileTransferService'

    id = Column(Integer, ForeignKey('CustomService.id'), primary_key=True)
    vendor = Column(String)
    operating_system = Column(String)
    content = Column(String)
    driver = Column(String)
    global_delay_factor = Column(Float, default=1.)
    device_multiprocessing = True

    driver_values = [(driver, driver) for driver in netmiko_drivers]

    __mapper_args__ = {
        'polymorphic_identity': 'netmiko_file_transfer_service',
    }

    @multiprocessing
    def job(self, task, device, results, incoming_payload):
        try:
            netmiko_handler = netmiko_connection(self, device)
            netmiko_handler.send_config_set(self.content.splitlines())
            result = f'configuration OK:\n\n{self.content}'
            success = True
            try:
                netmiko_handler.disconnect()
            except Exception:
                pass
        except Exception as e:
            result = f'netmiko config did not work because of {e}'
            success = False
        return success, result, incoming_payload


service_classes['Netmiko File Transfer Service'] = NetmikoFileTransferService

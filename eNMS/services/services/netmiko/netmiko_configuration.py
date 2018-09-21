from netmiko.ssh_dispatcher import CLASS_MAPPER
from sqlalchemy import Column, Float, ForeignKey, Integer, String

from eNMS.services.connections import netmiko_connection
from eNMS.services.models import Service, service_classes

netmiko_drivers = sorted(
    driver for driver in CLASS_MAPPER
    if 'telnet' not in driver and 'ssh' not in driver
)


class NetmikoConfigurationService(Service):

    __tablename__ = 'NetmikoConfigurationService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    vendor = Column(String)
    operating_system = Column(String)
    content = Column(String)
    driver = Column(String)
    global_delay_factor = Column(Float, default=1.)
    device_multiprocessing = True

    driver_values = [(driver, driver) for driver in netmiko_drivers]

    __mapper_args__ = {
        'polymorphic_identity': 'netmiko_configuration_service',
    }

    def job(self, incoming_payload):
        results = {}
        for device in self.task.compute_targets():
            try:
                netmiko_handler = netmiko_connection(self, device)
                netmiko_handler.send_config_set(self.content.splitlines())
                results[device.name] = f'configuration OK:\n\n{self.content}'
                success = True
                try:
                    netmiko_handler.disconnect()
                except Exception:
                    pass
            except Exception as e:
                result = f'netmiko config did not work because of {e}'
                success = False
        return success, results, incoming_payload


service_classes['Netmiko Configuration Service'] = NetmikoConfigurationService

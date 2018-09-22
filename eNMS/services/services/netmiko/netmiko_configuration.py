from multiprocessing.pool import ThreadPool
from sqlalchemy import Column, Float, ForeignKey, Integer, String

from eNMS.services.connections import netmiko_connection
from eNMS.services.helpers import netmiko_drivers
from eNMS.services.models import Service, service_classes


class NetmikoConfigurationService(Service):

    __tablename__ = 'NetmikoConfigurationService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    vendor = Column(String)
    operating_system = Column(String)
    content = Column(String)
    driver = Column(String)
    global_delay_factor = Column(Float, default=1.)
    driver_values = [(driver, driver) for driver in netmiko_drivers]

    __mapper_args__ = {
        'polymorphic_identity': 'netmiko_configuration_service',
    }

    def job(self, incoming_payload):
        results, global_success = {}, True
        for device in self.task.compute_targets():
            try:
                netmiko_handler = netmiko_connection(self, device)
                netmiko_handler.send_config_set(self.content.splitlines())
                results[device.name] = f'configuration OK ({self.content})'
                success = True
                try:
                    netmiko_handler.disconnect()
                except Exception:
                    pass
            except Exception as e:
                result, success = f'task failed ({e})', False
                global_success = False
            results[device.name] = {'success': success, 'result': result}
        results['success'] = global_success
        return results


service_classes['Netmiko Configuration Service'] = NetmikoConfigurationService

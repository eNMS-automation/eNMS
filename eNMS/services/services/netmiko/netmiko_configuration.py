from multiprocessing.pool import ThreadPool
from sqlalchemy import Column, Float, ForeignKey, Integer, String

from eNMS.services.helpers import netmiko_connection, netmiko_drivers
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

    def job(self, task, incoming_payload):
        targets = task.compute_targets()
        results = {'success': True}
        pool = ThreadPool(processes=len(targets))
        pool.map(self.device_job, [(device, results) for device in targets])
        pool.close()
        pool.join()
        return results

    def device_job(self, args):
        device, results = args
        try:
            netmiko_handler = netmiko_connection(self, device)
            netmiko_handler.send_config_set(self.content.splitlines())
            result, success = f'configuration OK ({self.content})', True
            try:
                netmiko_handler.disconnect()
            except Exception:
                pass
        except Exception as e:
            result, success = f'task failed ({e})', False
            results['success'] = False
        results[device.name] = {'success': success, 'result': result}


service_classes['Netmiko Configuration Service'] = NetmikoConfigurationService

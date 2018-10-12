from multiprocessing.pool import ThreadPool
from re import search
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from eNMS.automation.helpers import netmiko_connection, NETMIKO_DRIVERS
from eNMS.automation.models import Service, service_classes


class NetmikoValidationService(Service):

    __tablename__ = 'NetmikoValidationService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    content = Column(String)
    content_match = Column(String)
    content_match_regex = Column(Boolean)
    driver = Column(String)
    driver_values = NETMIKO_DRIVERS
    operating_system = Column(String)
    vendor = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'netmiko_validation_service',
    }

    def job(self, workflow_results=None):
        targets = self.compute_targets()
        results = {'success': True, 'devices': {}}
        pool = ThreadPool(processes=len(targets))
        pool.map(self.device_job, [(device, results) for device in targets])
        pool.close()
        pool.join()
        return results

    def device_job(self, args):
        device, results = args
        success, result = True, {}
        try:
            netmiko_handler = netmiko_connection(self, device)
            output = netmiko_handler.send_command(self.content)
            if self.content_match_regex:
                if not bool(search(self.content_match, str(output))):
                    success = False
            else:
                if self.content_match not in str(output):
                    success = False
            result[command] = {
                'output': output,
                'expected': self.content_match,
                'success': success
            }
            try:
                netmiko_handler.disconnect()
            except Exception:
                pass
        except Exception as e:
            result, success = f'service failed ({e})', False
            results['success'] = False
        results['devices'][device.name] = {
            'success': success,
            'result': result
        }


service_classes['netmiko_validation_service'] = NetmikoValidationService

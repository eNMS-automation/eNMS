from multiprocessing.pool import ThreadPool
from re import search
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from eNMS.services.helpers import netmiko_connection, netmiko_drivers
from eNMS.services.models import Service, service_classes


class NetmikoValidationService(Service):

    __tablename__ = 'NetmikoValidationService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    vendor = Column(String)
    operating_system = Column(String)
    driver = Column(String)
    command1 = Column(String)
    command2 = Column(String)
    command3 = Column(String)
    content_match1 = Column(String)
    content_match2 = Column(String)
    content_match3 = Column(String)
    content_match_regex1 = Column(Boolean)
    content_match_regex2 = Column(Boolean)
    content_match_regex3 = Column(Boolean)
    driver_values = [(driver, driver) for driver in netmiko_drivers]

    __mapper_args__ = {
        'polymorphic_identity': 'netmiko_validation_service',
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
        success, result = True, {}
        try:
            netmiko_handler = netmiko_connection(self, device)
            for i in range(1, 4):
                command = getattr(self, 'command' + str(i))
                if not command:
                    continue
                output = netmiko_handler.send_command(command)
                expected = getattr(self, 'content_match' + str(i))
                result[command] = {'output': output, 'expected': expected}
                if getattr(self, 'content_match_regex' + str(i)):
                    if not bool(search(expected, str(output))):
                        results['success'], success = False, False
                else:
                    if expected not in str(output):
                        results['success'], success = False, False
            try:
                netmiko_handler.disconnect()
            except Exception:
                pass
        except Exception as e:
            result, success = f'task failed ({e})', False
            results['success'] = False
        results[device.name] = {'success': success, 'result': result}


service_classes['Netmiko Validation Service'] = NetmikoValidationService

from netmiko.ssh_dispatcher import CLASS_MAPPER
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from eNMS.services.connections import netmiko_connection
from eNMS.services.custom_service import CustomService, service_classes
from eNMS.services.models import multiprocessing

netmiko_drivers = sorted(
    driver for driver in CLASS_MAPPER
    if 'telnet' not in driver and 'ssh' not in driver
)


class NetmikoValidationService(CustomService):

    __tablename__ = 'NetmikoValidationService'

    id = Column(Integer, ForeignKey('CustomService.id'), primary_key=True)
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
    device_multiprocessing = True

    driver_values = [(driver, driver) for driver in netmiko_drivers]

    __mapper_args__ = {
        'polymorphic_identity': 'netmiko_validation_service',
    }

    @multiprocessing
    def job(self, task, device, results, incoming_payload):
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
                        success = False
                else:
                    if expected not in str(output):
                        success = False
            try:
                netmiko_handler.disconnect()
            except Exception:
                pass
        except Exception as e:
            result = f'netmiko did not work because of {e}'
            success = False
        return success, result, incoming_payload


service_classes['Netmiko Validation Service'] = NetmikoValidationService

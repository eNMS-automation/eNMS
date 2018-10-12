from multiprocessing.pool import ThreadPool
from re import search
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from eNMS.automation.helpers import netmiko_connection, NETMIKO_DRIVERS
from eNMS.automation.models import Service, service_classes


class NetmikoValidationService(Service):

    __tablename__ = 'NetmikoValidationService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = True
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

    def job(self, device, results, payload):
        netmiko_handler = netmiko_connection(self, device)
        output = netmiko_handler.send_command(self.content)
        if self.content_match_regex:
            if not bool(search(self.content_match, str(output))):
                success = False
        else:
            if self.content_match not in str(output):
                success = False
        netmiko_handler.disconnect()
        return {
            'output': output,
            'expected': self.content_match,
            'success': success,
        }


service_classes['netmiko_validation_service'] = NetmikoValidationService

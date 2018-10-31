from re import search
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String

from eNMS.automation.helpers import (
    netmiko_connection,
    NETMIKO_DRIVERS,
    substitute
)
from eNMS.automation.models import Service
from eNMS.base.models import service_classes


class NetmikoValidationService(Service):

    __tablename__ = 'NetmikoValidationService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    multiprocessing = True
    command = Column(String)
    content_match = Column(String)
    content_match_regex = Column(Boolean)
    driver = Column(String)
    driver_values = NETMIKO_DRIVERS
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=1.)
    global_delay_factor = Column(Float, default=1.)

    __mapper_args__ = {
        'polymorphic_identity': 'netmiko_validation_service',
    }

    def job(self, device, payload):
        netmiko_handler = netmiko_connection(self, device)
        command = substitute(self.command, locals())
        output = netmiko_handler.send_command(command)
        success = (
            self.content_match_regex and search(self.content_match, output)
            or self.content_match in output and not self.content_match_regex
        )
        netmiko_handler.disconnect()
        return {
            'output': output,
            'expected': self.content_match,
            'success': success,
        }


service_classes['netmiko_validation_service'] = NetmikoValidationService

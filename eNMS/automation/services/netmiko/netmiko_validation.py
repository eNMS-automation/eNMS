from re import search
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String

from eNMS.automation.helpers import (
    netmiko_connection,
    NETMIKO_DRIVERS,
    substitute
)
from eNMS.automation.models import Service
from eNMS.base.classes import service_classes


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
        'polymorphic_identity': 'NetmikoValidationService',
    }

    def job(self, device, payload):
        netmiko_handler = netmiko_connection(self, device)
        command = substitute(self.command, locals())
        res = netmiko_handler.send_command(command)
        success = (
            self.content_match_regex and bool(search(self.content_match, res))
            or self.content_match in res and not self.content_match_regex
        )
        netmiko_handler.disconnect()
        return {
            'output': res,
            'expected': self.content_match,
            'success': success,
        }


service_classes['NetmikoValidationService'] = NetmikoValidationService

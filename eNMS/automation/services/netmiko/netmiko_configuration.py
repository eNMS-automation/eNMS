from sqlalchemy import Column, Float, ForeignKey, Integer, String

from eNMS.automation.helpers import (
    netmiko_connection,
    NETMIKO_DRIVERS,
    substitute
)
from eNMS.automation.models import Service, service_classes


class NetmikoConfigurationService(Service):

    __tablename__ = 'NetmikoConfigurationService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = True
    vendor = Column(String)
    operating_system = Column(String)
    content = Column(String)
    content_textarea = True
    driver = Column(String)
    driver_values = NETMIKO_DRIVERS
    global_delay_factor = Column(Float, default=1.)

    __mapper_args__ = {
        'polymorphic_identity': 'netmiko_configuration_service',
    }

    def job(self, device, payload):
        netmiko_handler = netmiko_connection(self, device)
        netmiko_handler.enable()
        config = substitute(self.content, locals())
        netmiko_handler.send_config_set(config.splitlines())
        netmiko_handler.disconnect()
        return {'success': True, 'result': f'configuration OK {config}'}


service_classes['netmiko_configuration_service'] = NetmikoConfigurationService

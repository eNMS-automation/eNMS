from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String

from eNMS.automation.helpers import (
    netmiko_connection,
    NETMIKO_DRIVERS,
    substitute
)
from eNMS.automation.models import Service
from eNMS.base.models import service_classes


class NetmikoConfigurationService(Service):

    __tablename__ = 'NetmikoConfigurationService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    multiprocessing = True
    content = Column(String)
    content_textarea = True
    driver = Column(String)
    driver_values = NETMIKO_DRIVERS
    enable_mode = Column(Boolean)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=1.)
    global_delay_factor = Column(Float, default=1.)

    __mapper_args__ = {
        'polymorphic_identity': 'netmiko_configuration_service',
    }

    def job(self, device, payload):
        netmiko_handler = netmiko_connection(self, device)
        if self.enable_mode:
            netmiko_handler.enable()
        config = substitute(self.content, locals())
        netmiko_handler.send_config_set(config.splitlines())
        netmiko_handler.disconnect()
        return {'success': True, 'result': f'configuration OK {config}'}


service_classes['netmiko_configuration_service'] = NetmikoConfigurationService

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String

from eNMS.automation.helpers import NETMIKO_DRIVERS
from eNMS.automation.models import Service
from eNMS.base.classes import service_classes


class NetmikoConfigurationService(Service):

    __tablename__ = 'NetmikoConfigurationService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = True
    content = Column(String)
    content_textarea = True
    driver = Column(String)
    driver_values = NETMIKO_DRIVERS
    use_device_driver = Column(Boolean, default=True)
    enable_mode = Column(Boolean)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=1.)
    global_delay_factor = Column(Float, default=1.)

    __mapper_args__ = {
        'polymorphic_identity': 'NetmikoConfigurationService',
    }

    def job(self, device, _):
        netmiko_handler = self.netmiko_connection(device)
        if self.enable_mode:
            netmiko_handler.enable()
        config = self.sub(self.content, locals())
        netmiko_handler.send_config_set(config.splitlines())
        netmiko_handler.disconnect()
        return {'success': True, 'result': f'configuration OK {config}'}


service_classes['NetmikoConfigurationService'] = NetmikoConfigurationService

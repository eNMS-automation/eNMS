from datetime import datetime
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String

from eNMS.automation.helpers import NETMIKO_DRIVERS
from eNMS.automation.models import Service
from eNMS.base.classes import service_classes


class ConfigurationBackupService(Service):

    __tablename__ = 'ConfigurationBackupService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = True
    number_of_configuration = Column(Integer, default=10)
    driver = Column(String)
    driver_values = NETMIKO_DRIVERS
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=10.)
    global_delay_factor = Column(Float, default=1.)

    __mapper_args__ = {
        'polymorphic_identity': 'ConfigurationBackupService',
    }

    def job(self, device, _):
        now = datetime.now()
        try:
            netmiko_handler = self.netmiko_connection(device)
            netmiko_handler.enable()
            config = netmiko_handler.send_command(device.configuration_command)
            device.last_status, device.last_update = 'Success', now
        except Exception as e:
            device.last_status, device.last_update = 'Failure', now
            return {'success': False, 'result': str(e)}
        device.configurations[now] = config
        if len(device.configurations) > self.number_of_configuration:
            device.configurations.pop(min(device.configurations))
        return {
            'success': True,
            'result': f'Command: {device.configuration_command}'
        }


service_classes['ConfigurationBackupService'] = ConfigurationBackupService

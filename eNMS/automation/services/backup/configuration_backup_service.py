from datetime import datetime
from pathlib import Path
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
        path_configurations = Path.cwd() / 'git' / 'configurations'
        try:
            netmiko_handler = self.netmiko_connection(device)
            try:
                netmiko_handler.enable()
            except Exception:
                pass
            config = netmiko_handler.send_command(device.configuration_command)
            device.last_status = 'Success'
            device.last_runtime = (datetime.now() - now).total_seconds()
            netmiko_handler.disconnect()
            if device.configurations:
                last_config = device.configurations[max(device.configurations)]
                if config == last_config:
                    return {'success': True, 'result': 'no change'}
            device.configurations[now] = config
            with open(path_configurations / device.name, 'w') as file:
                file.write(config)
            device.last_update = now
        except Exception as e:
            device.last_status, device.last_update = 'Failure', now
            device.last_failure = now
            return {'success': False, 'result': str(e)}
        if len(device.configurations) > self.number_of_configuration:
            device.configurations.pop(min(device.configurations))
        return {
            'success': True,
            'result': f'Command: {device.configuration_command}'
        }


service_classes['ConfigurationBackupService'] = ConfigurationBackupService

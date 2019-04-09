from datetime import datetime
from pathlib import Path
from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict
from yaml import dump

from eNMS.automation.functions import NAPALM_DRIVERS
from eNMS.automation.models import Service
from eNMS.classes import service_classes
from eNMS.functions import str_dict
from eNMS.inventory.models import Device


class NapalmBackupService(Service):

    __tablename__ = "NapalmBackupService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    configuration_backup_service = True
    has_targets = True
    number_of_configuration = Column(Integer, default=10)
    driver = Column(String(255))
    driver_values = NAPALM_DRIVERS
    use_device_driver = Column(Boolean, default=True)
    optional_args = Column(MutableDict.as_mutable(PickleType), default={})

    __mapper_args__ = {"polymorphic_identity": "NapalmBackupService"}

    def generate_yaml_file(self, path, device):
        data = {
            "last_failure": device.last_failure,
            "last_runtime": device.last_runtime,
            "last_update": device.last_update,
            "last_status": device.last_status,
        }
        with open(path / "data.yml", "w") as file:
            dump(data, file, default_flow_style=False)

    def job(self, payload: dict, device: Device) -> dict:
        try:
            now = datetime.now()
            path_configurations = Path.cwd() / "git" / "configurations"
            path_device_config = path_configurations / device.name
            path_device_config.mkdir(parents=True, exist_ok=True)
            napalm_driver = self.napalm_connection(device)
            napalm_driver.open()
            self.logs.append(f"Fetching configuration on {device.name} (Napalm)")
            config = str_dict(napalm_driver.get_config())
            napalm_driver.close()
            device.last_status = "Success"
            device.last_runtime = (datetime.now() - now).total_seconds()
            if device.configurations:
                last_config = device.configurations[max(device.configurations)]
                if config == last_config:
                    return {"success": True, "result": "no change"}
            device.configurations[now] = device.current_configuration = config
            with open(path_device_config / device.name, "w") as file:
                file.write(config)
            device.last_update = now
            self.generate_yaml_file(path_device_config, device)
        except Exception as e:
            device.last_status = "Failure"
            device.last_failure = now
            self.generate_yaml_file(path_device_config, device)
            return {"success": False, "result": str(e)}
        if len(device.configurations) > self.number_of_configuration:
            device.configurations.pop(min(device.configurations))
        return {"success": True, "result": "Get Config via Napalm"}


service_classes["NapalmBackupService"] = NapalmBackupService

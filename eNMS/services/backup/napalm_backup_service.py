from datetime import datetime
from pathlib import Path
from ruamel import yaml
from sqlalchemy import Boolean, ForeignKey, Integer
from wtforms import HiddenField, IntegerField

from eNMS import app
from eNMS.database.dialect import Column, MutableDict, SmallString
from eNMS.forms.automation import ServiceForm
from eNMS.forms.services import NapalmForm
from eNMS.models.automation import Run, Service
from eNMS.models.inventory import Device


class NapalmBackupService(Service):

    __tablename__ = "NapalmBackupService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    configuration_backup_service = True
    has_targets = True
    number_of_configuration = Column(Integer, default=10)
    driver = Column(SmallString)
    use_device_driver = Column(Boolean, default=True)
    optional_args = Column(MutableDict)

    __mapper_args__ = {"polymorphic_identity": "NapalmBackupService"}

    def generate_yaml_file(self, path, device):
        data = {
            "last_failure": device.last_failure,
            "last_runtime": device.last_runtime,
            "last_update": device.last_update,
            "last_status": device.last_status,
        }
        with open(path / "data.yml", "w") as file:
            yaml.dump(data, file, default_flow_style=False)

    def job(self, run: "Run", payload: dict, device: Device) -> dict:
        try:
            now = datetime.now()
            path_configurations = Path.cwd() / "git" / "configurations"
            path_device_config = path_configurations / device.name
            path_device_config.mkdir(parents=True, exist_ok=True)
            napalm_connection = run.napalm_connection(device)
            run.log("info", f"Fetching configuration on {device.name} (Napalm)")
            config = app.str_dict(napalm_connection.get_config())
            device.last_status = "Success"
            device.last_runtime = (datetime.now() - now).total_seconds()
            if device.configurations:
                last_config = device.configurations[max(device.configurations)]
                if config == last_config:
                    return {"success": True, "result": "no change"}
            device.configurations[str(now)] = device.current_configuration = config
            with open(path_device_config / device.name, "w") as file:
                file.write(config)
            device.last_update = str(now)
            self.generate_yaml_file(path_device_config, device)
        except Exception as e:
            device.last_status = "Failure"
            device.last_failure = str(now)
            self.generate_yaml_file(path_device_config, device)
            return {"success": False, "result": str(e)}
        if len(device.configurations) > self.number_of_configuration:
            device.configurations.pop(min(device.configurations))
        return {"success": True, "result": "Get Config via Napalm"}


class NapalmBackupForm(ServiceForm, NapalmForm):
    form_type = HiddenField(default="NapalmBackupService")
    number_of_configuration = IntegerField(default=10)

from datetime import datetime
from pathlib import Path
from ruamel import yaml
from sqlalchemy import Boolean, ForeignKey, Integer
from wtforms import HiddenField

from eNMS import app
from eNMS.database.dialect import Column, MutableDict, SmallString
from eNMS.forms.automation import ServiceForm
from eNMS.forms.services import NapalmForm
from eNMS.models.automation import ConnectionService


class NapalmBackupService(ConnectionService):

    __tablename__ = "napalm_backup_service"

    id = Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    configuration_backup_service = True
    driver = Column(SmallString)
    use_device_driver = Column(Boolean, default=True)
    optional_args = Column(MutableDict)

    __mapper_args__ = {"polymorphic_identity": "napalm_backup_service"}

    def generate_yaml_file(self, path, device):
        data = {
            "last_failure": device.last_failure,
            "last_runtime": device.last_runtime,
            "last_update": device.last_update,
            "last_status": device.last_status,
        }
        with open(path / "data.yml", "w") as file:
            yaml.dump(data, file, default_flow_style=False)

    def job(self, run, payload, device):
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
            if config == device.configuration:
                return {"success": True, "result": "no change"}
            device.configuration = config
            with open(path_device_config / device.name, "w") as file:
                file.write(config)
            device.last_update = str(now)
            self.generate_yaml_file(path_device_config, device)
        except Exception as e:
            device.last_status = "Failure"
            device.last_failure = str(now)
            self.generate_yaml_file(path_device_config, device)
            return {"success": False, "result": str(e)}
        return {"success": True, "result": "Get Config via Napalm"}


class NapalmBackupForm(ServiceForm, NapalmForm):
    form_type = HiddenField(default="napalm_backup_service")

from datetime import datetime
from pathlib import Path
from ruamel import yaml
from sqlalchemy import Boolean, Float, ForeignKey, Integer
from wtforms import HiddenField, IntegerField, StringField

from eNMS.database import Session
from eNMS.database.dialect import Column, SmallString
from eNMS.forms.automation import ServiceForm
from eNMS.forms.services import NetmikoForm
from eNMS.models.automation import Run, Service
from eNMS.models.inventory import Device


class NetmikoBackupService(Service):

    __tablename__ = "NetmikoBackupService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    configuration_backup_service = True
    has_targets = True
    privileged_mode = Column(Boolean, default=False)
    number_of_configuration = Column(Integer, default=10)
    configuration_command = Column(SmallString)
    driver = Column(SmallString)
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=10.0)
    global_delay_factor = Column(Float, default=1.0)

    __mapper_args__ = {"polymorphic_identity": "NetmikoBackupService"}

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
            netmiko_connection = run.netmiko_connection(device)
            try:
                netmiko_connection.enable()
            except Exception:
                pass
            run.log("info", f"Fetching configuration on {device.name} (Netmiko)")
            command = run.configuration_command
            config = netmiko_connection.send_command(command)
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
        Session.commit()
        return {"success": True, "result": f"Command: {command}"}


class NetmikoBackupForm(ServiceForm, NetmikoForm):
    form_type = HiddenField(default="NetmikoBackupService")
    number_of_configuration = IntegerField(default=10)
    configuration_command = StringField()
    groups = {
        "Main Parameters": ["number_of_configuration", "configuration_command"],
        "Netmiko Parameters": NetmikoForm.group,
    }

from datetime import datetime
from pathlib import Path
from ruamel import yaml
from sqlalchemy import Boolean, Float, ForeignKey, Integer
from wtforms import HiddenField, StringField

from eNMS.database import Session
from eNMS.database.dialect import Column, SmallString
from eNMS.database.functions import factory
from eNMS.forms.automation import ServiceForm
from eNMS.forms.services import NetmikoForm
from eNMS.models.automation import ConnectionService


class NetmikoBackupService(ConnectionService):

    __tablename__ = "netmiko_backup_service"
    pretty_name = "Netmiko Backup"

    id = Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    privileged_mode = Column(Boolean, default=False)
    configuration_command = Column(SmallString)
    driver = Column(SmallString)
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=10.0)
    global_delay_factor = Column(Float, default=1.0)

    __mapper_args__ = {"polymorphic_identity": "netmiko_backup_service"}

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
            device.last_runtime = datetime.now()
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
            configuration = netmiko_connection.send_command(command)
            device.last_status = "Success"
            device.last_duration = (
                f"{(datetime.now() - device.last_runtime).total_seconds()}s"
            )
            if configuration == device.configuration:
                return {"success": True, "result": "no change"}
            device.last_update = str(device.last_runtime)
            factory(
                "configuration",
                device=device.id,
                runtime=device.last_runtime,
                duration=device.last_duration,
                configuration=configuration,
            )
            device.configuration = configuration
            with open(path_device_config / device.name, "w") as file:
                file.write(configuration)
            self.generate_yaml_file(path_device_config, device)
        except Exception as e:
            device.last_status = "Failure"
            device.last_failure = str(device.last_runtime)
            self.generate_yaml_file(path_device_config, device)
            return {"success": False, "result": str(e)}
        return {"success": True, "result": f"Command: {command}"}


class NetmikoBackupForm(ServiceForm, NetmikoForm):
    form_type = HiddenField(default="netmiko_backup_service")
    configuration_command = StringField()
    groups = {
        "Main Parameters": {
            "commands": ["configuration_command"],
            "default": "expanded",
        },
        "Netmiko Parameters": NetmikoForm.group,
    }

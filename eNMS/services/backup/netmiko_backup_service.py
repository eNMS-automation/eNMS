from datetime import datetime
from pathlib import Path
from sqlalchemy import Boolean, Float, ForeignKey, Integer
from wtforms import HiddenField, StringField

from eNMS.database.dialect import Column, SmallString
from eNMS.database.functions import factory
from eNMS.forms.automation import NetmikoForm
from eNMS.models.automation import ConnectionService


class NetmikoBackupService(ConnectionService):

    __tablename__ = "netmiko_backup_service"
    pretty_name = "Netmiko Backup"

    id = Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    enable_mode = Column(Boolean, default=True)
    config_mode = Column(Boolean, default=False)
    configuration_command = Column(SmallString)
    driver = Column(SmallString)
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=10.0)
    global_delay_factor = Column(Float, default=1.0)
    regex_pattern_1 = Column(SmallString)
    regex_replace_1 = Column(SmallString)
    regex_pattern_2 = Column(SmallString)
    regex_replace_2 = Column(SmallString)
    regex_pattern_3 = Column(SmallString)
    regex_replace_3 = Column(SmallString)

    __mapper_args__ = {"polymorphic_identity": "netmiko_backup_service"}

    def job(self, run, payload, device):
        try:
            device.last_runtime = datetime.now()
            path_configurations = Path.cwd() / "git" / "configurations"
            path_device_config = path_configurations / device.name
            path_device_config.mkdir(parents=True, exist_ok=True)
            netmiko_connection = run.netmiko_connection(device)
            run.log("info", f"Fetching configuration on {device.name} (Netmiko)")
            command = run.configuration_command
            configuration = netmiko_connection.send_command(command)
            device.last_status = "Success"
            device.last_duration = (
                f"{(datetime.now() - device.last_runtime).total_seconds()}s"
            )
            if run.transform(device.configuration) == run.transform(configuration):
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
            run.generate_yaml_file(path_device_config, device)
        except Exception as e:
            device.last_status = "Failure"
            device.last_failure = str(device.last_runtime)
            run.generate_yaml_file(path_device_config, device)
            return {"success": False, "result": str(e)}
        return {"success": True, "result": f"Command: {command}"}


class NetmikoBackupForm(NetmikoForm):
    form_type = HiddenField(default="netmiko_backup_service")
    configuration_command = StringField()
    regex_pattern_1 = StringField("First regex to change config results")
    regex_replace_1 = StringField("Value to replace first regex")
    regex_pattern_2 = StringField("Second regex to change config results")
    regex_replace_2 = StringField("Value to replace second regex")
    regex_pattern_3 = StringField("Third regex to change config results")
    regex_replace_3 = StringField("Value to replace third regex")
    groups = {
        "Main Parameters": {
            "commands": [
                "configuration_command",
                "regex_pattern_1",
                "regex_replace_1",
                "regex_pattern_2",
                "regex_replace_2",
                "regex_pattern_3",
                "regex_replace_1",
            ],
            "default": "expanded",
        },
        **NetmikoForm.groups,
    }

from datetime import datetime
from flask_wtf import FlaskForm
from pathlib import Path
from re import M, sub
from sqlalchemy import Boolean, Float, ForeignKey, Integer
from wtforms import FormField

from eNMS.database import db
from eNMS.forms.automation import NetmikoForm
from eNMS.forms.fields import FieldList, HiddenField, StringField
from eNMS.models.automation import ConnectionService


class DataBackupService(ConnectionService):

    __tablename__ = "data_backup_service"
    pretty_name = "Netmiko Operational Data Backup"
    parent_type = "connection_service"
    id = db.Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    enable_mode = db.Column(Boolean, default=True)
    config_mode = db.Column(Boolean, default=False)
    driver = db.Column(db.SmallString)
    use_device_driver = db.Column(Boolean, default=True)
    fast_cli = db.Column(Boolean, default=False)
    timeout = db.Column(Integer, default=10.0)
    global_delay_factor = db.Column(Float, default=1.0)
    configuration_command = db.Column(db.LargeString)
    operational_data_command = db.Column(db.List)
    replacements = db.Column(db.List)

    __mapper_args__ = {"polymorphic_identity": "data_backup_service"}

    def job(self, run, payload, device):
        path = Path.cwd() / "network_data" / device.name
        path.mkdir(parents=True, exist_ok=True)
        try:
            device.last_runtime = datetime.now()
            netmiko_connection = run.netmiko_connection(device)
            run.log("info", "Fetching Operational Data", device)
            for data in ("configuration", "operational_data"):
                value = run.sub(getattr(self, f"{data}_command"), locals())
                if data == "configuration":
                    result = netmiko_connection.send_command(value)
                    for r in self.replacements:
                        result = sub(r["pattern"], r["replace_with"], result, flags=M)
                else:
                    result = []
                    for cmd_dict in value:
                        command, prefix = cmd_dict["command"], cmd_dict["prefix"]
                        if not command:
                            continue
                        title = f"CMD '{command.upper()}'"
                        if prefix:
                            title += f" [{prefix}]"
                        header = (
                            f"\n{' ' * 30}{title}\n" f"{' ' * 30}{'*' * len(title)}"
                        )
                        command_result = [f"{header}\n\n"]
                        for line in netmiko_connection.send_command(
                            command
                        ).splitlines():
                            if prefix:
                                line = f"{prefix} - {line}"
                            command_result.append(line)
                        result.append("\n".join(command_result))
                    result = "\n\n".join(result)
                if not result:
                    continue
                setattr(device, data, result)
                with open(path / data, "w") as file:
                    file.write(result)
            device.last_status = "Success"
            device.last_duration = (
                f"{(datetime.now() - device.last_runtime).total_seconds()}s"
            )
            device.last_update = str(device.last_runtime)
            run.generate_yaml_file(path, device)
        except Exception as exc:
            device.last_status = "Failure"
            device.last_failure = str(device.last_runtime)
            run.generate_yaml_file(path, device)
            return {"success": False, "result": str(exc)}
        return {"success": True}


class ReplacementForm(FlaskForm):
    pattern = StringField("Pattern")
    replace_with = StringField("Replace With")


class OperationalDataForm(FlaskForm):
    command = StringField("Operational Data Command")
    prefix = StringField("Label")


class DataBackupForm(NetmikoForm):
    form_type = HiddenField(default="data_backup_service")
    configuration_command = StringField("Command to retrieve the configuration")
    operational_data_command = FieldList(FormField(OperationalDataForm), min_entries=12)
    replacements = FieldList(FormField(ReplacementForm), min_entries=12)
    groups = {
        "Create Configuration File": {
            "commands": ["configuration_command"],
            "default": "expanded",
        },
        "Create Operational Data File": {
            "commands": ["operational_data_command"],
            "default": "expanded",
        },
        "Search Response & Replace": {
            "commands": ["replacements"],
            "default": "expanded",
        },
        **NetmikoForm.groups,
    }

from datetime import datetime
from flask_wtf import FlaskForm
from pathlib import Path
from re import M, sub
from sqlalchemy import Boolean, Float, ForeignKey, Integer
from wtforms import FormField

from eNMS import app
from eNMS.database import db
from eNMS.forms.automation import NetmikoForm
from eNMS.forms.fields import FieldList, HiddenField, SelectField, StringField
from eNMS.models.automation import ConnectionService


class NetmikoBackupService(ConnectionService):

    __tablename__ = "netmiko_backup_service"
    pretty_name = "Netmiko Data Backup"
    parent_type = "connection_service"
    id = db.Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    enable_mode = db.Column(Boolean, default=True)
    config_mode = db.Column(Boolean, default=False)
    driver = db.Column(db.SmallString)
    use_device_driver = db.Column(Boolean, default=True)
    fast_cli = db.Column(Boolean, default=False)
    timeout = db.Column(Integer, default=10.0)
    global_delay_factor = db.Column(Float, default=1.0)
    property = db.Column(db.SmallString)
    commands = db.Column(db.List)
    replacements = db.Column(db.List)

    __mapper_args__ = {"polymorphic_identity": "netmiko_backup_service"}

    def job(self, run, payload, device):
        path = Path.cwd() / "network_data" / device.name
        path.mkdir(parents=True, exist_ok=True)
        try:
            device.last_runtime = datetime.now()
            netmiko_connection = run.netmiko_connection(device)
            commands = run.sub(self.commands, locals())
            result = []
            for command in commands:
                if not command["value"]:
                    continue
                run.log("info", f"Running command '{command['value']}'", device)
                title = f"COMMAND '{command['value'].upper()}'"
                if command["prefix"]:
                    title += f" [{command['prefix']}]"
                header = f"\n{' ' * 30}{title}\n" f"{' ' * 30}{'*' * len(title)}"
                command_result = [f"{header}\n\n"]
                for line in netmiko_connection.send_command(
                    command["value"]
                ).splitlines():
                    if command["prefix"]:
                        line = f"{command['prefix']} - {line}"
                    command_result.append(line)
                result.append("\n".join(command_result))
            result = "\n\n".join(result)
            for r in self.replacements:
                result = sub(r["pattern"], r["replace_with"], result, flags=M)
            setattr(device, self.property, result)
            with open(path / self.property, "w") as file:
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


class CommandsForm(FlaskForm):
    value = StringField("Command")
    prefix = StringField("Label")


class DataBackupForm(NetmikoForm):
    form_type = HiddenField(default="netmiko_backup_service")
    property = SelectField(
        "Configuration Property to Update",
        choices=list(app.configuration_properties.items()),
    )
    commands = FieldList(FormField(CommandsForm), min_entries=12)
    replacements = FieldList(FormField(ReplacementForm), min_entries=12)
    groups = {
        "Target property and commands": {
            "commands": ["property", "commands"],
            "default": "expanded",
        },
        "Search Response & Replace": {
            "commands": ["replacements"],
            "default": "expanded",
        },
        **NetmikoForm.groups,
    }

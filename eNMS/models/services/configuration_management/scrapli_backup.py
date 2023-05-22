from datetime import datetime
from pathlib import Path
from re import M, sub
from sqlalchemy import Boolean, Float, ForeignKey, Integer
from sqlalchemy.orm import load_only
from wtforms import FormField

from eNMS.database import db
from eNMS.forms import ScrapliForm, CommandsForm, ReplacementForm
from eNMS.fields import BooleanField, FieldList, HiddenField, SelectField, StringField
from eNMS.models.automation import ConnectionService
from eNMS.variables import vs
from traceback import format_exc


class ScrapliBackupService(ConnectionService):
    __tablename__ = "scrapli_backup_service"
    pretty_name = "Scrapli Data Backup"
    parent_type = "connection_service"
    id = db.Column(Integer, ForeignKey("connection_service.id"), primary_key=True)

    is_configuration = db.Column(Boolean, default=False)
    driver = db.Column(db.SmallString)
    transport = db.Column(db.SmallString, default="system")
    timeout_socket = db.Column(Float, default=15.0)
    timeout_transport = db.Column(Float, default=30.0)
    timeout_ops = db.Column(Float, default=30.0)
    local_path = db.Column(db.SmallString, default="network_data")
    property = db.Column(db.SmallString)
    commands = db.Column(db.List)
    replacements = db.Column(db.List)
    add_header = db.Column(Boolean, default=True)

    __mapper_args__ = {"polymorphic_identity": "scrapli_backup_service"}

    def job(self, run, device):
        local_path = run.sub(run.local_path, locals())
        path = Path.cwd() / local_path / device.name
        path.mkdir(parents=True, exist_ok=True)
        try:
            runtime = datetime.now()
            setattr(device, f"last_{self.property}_runtime", str(runtime))
            scrapli_connection = run.scrapli_connection(device)
            commands = run.sub(self.commands, locals())
            result = []
            for command in commands:
                if not command["value"]:
                    continue
                run.log(
                    "info",
                    f"Running command '{command['value']}'",
                    device,
                    logger="security",
                )
                title = f"COMMAND '{command['value'].upper()}'"
                if command["prefix"]:
                    title += f" [{command['prefix']}]"
                header = f"\n{' ' * 30}{title}\n" f"{' ' * 30}{'*' * len(title)}"
                command_result = [f"{header}\n\n"] if self.add_header else []
                for line in scrapli_connection.send_command(
                    command["value"]
                ).result.splitlines():
                    if command["prefix"]:
                        line = f"{command['prefix']} - {line}"
                    command_result.append(line)
                result.append("\n".join(command_result))
            result = "\n\n".join(result)
            for replacement in self.replacements:
                result = sub(
                    replacement["pattern"], replacement["replace_with"], result, flags=M
                )
            device_with_deferred_data = (
                db.query("device")
                .options(load_only(getattr(vs.models["device"], self.property)))
                .filter_by(id=device.id)
                .one()
            )
            setattr(device, f"last_{self.property}_status", "Success")
            duration = f"{(datetime.now() - runtime).total_seconds()}s"
            setattr(device, f"last_{self.property}_duration", duration)
            if getattr(device_with_deferred_data, self.property) != result:
                setattr(device_with_deferred_data, self.property, result)
                with open(path / self.property, "w") as file:
                    file.write(result)
                setattr(device, f"last_{self.property}_update", str(runtime))
        except Exception:
            setattr(device, f"last_{self.property}_status", "Failure")
            setattr(device, f"last_{self.property}_failure", str(runtime))
            return {"success": False, "result": format_exc()}
        run.update_configuration_properties(path, self.property, device)
        return {"success": True}


class ScrapliBackupForm(ScrapliForm):
    form_type = HiddenField(default="scrapli_backup_service")
    property = SelectField(
        "Configuration Property to Update",
        choices=list(vs.configuration_properties.items()),
    )
    local_path = StringField("Local Path", default="network_data", substitution=True)
    commands = FieldList(FormField(CommandsForm), min_entries=12)
    replacements = FieldList(FormField(ReplacementForm), min_entries=12)
    add_header = BooleanField("Add header for each command", default=True)
    groups = {
        "Target property and commands": {
            "commands": ["property", "local_path", "add_header", "commands"],
            "default": "expanded",
        },
        "Search Response & Replace": {
            "commands": ["replacements"],
            "default": "expanded",
        },
        **ScrapliForm.groups,
    }

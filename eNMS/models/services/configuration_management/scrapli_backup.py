from datetime import datetime
from pathlib import Path
from re import M, sub
from sqlalchemy import Boolean, Float, ForeignKey, Integer
from traceback import format_exc
from wtforms import FormField

from eNMS.database import db
from eNMS.fields import BooleanField, FieldList, HiddenField, SelectField, StringField
from eNMS.forms import CommandsForm, ReplacementForm, ScrapliForm
from eNMS.models.automation import ConnectionService
from eNMS.variables import vs


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
    local_path = db.Column(
        db.SmallString, default=vs.automation["configuration_backup"]["folder"]
    )
    property = db.Column(db.SmallString)
    commands = db.Column(db.List)
    replacements = db.Column(db.List)
    add_header = db.Column(Boolean, default=True)

    __mapper_args__ = {"polymorphic_identity": "scrapli_backup_service"}

    @staticmethod
    def job(self, run, device):
        local_path = run.sub(run.local_path, locals())
        commands = run.sub(self.commands, locals())
        if run.dry_run:
            return {"local_path": local_path, "commands": commands}
        path = Path.cwd() / local_path / device.name
        path.mkdir(parents=True, exist_ok=True)
        kwargs = {"success": True, "runtime": datetime.now()}
        try:
            scrapli_connection = run.scrapli_connection(device)
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
        except Exception:
            result, kwargs["success"] = format_exc(), False
        kwargs["result"] = result
        with db.session_scope(remove=run.high_performance and run.in_process):
            write_config = run.configuration_transaction(
                self.property, device, **kwargs
            )
        if write_config:
            with open(path / self.property, "w") as file:
                file.write(result)
        if kwargs["success"]:
            run.update_configuration_properties(path, self.property, device)
            return {"success": True}
        else:
            return {key: kwargs[key] for key in ("success", "result")}


class ScrapliBackupForm(ScrapliForm):
    form_type = HiddenField(default="scrapli_backup_service")
    property = SelectField(
        "Configuration Property to Update",
        choices=list(vs.configuration_properties.items()),
    )
    local_path = StringField(
        "Local Path",
        default=vs.automation["configuration_backup"]["folder"],
        substitution=True,
    )
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

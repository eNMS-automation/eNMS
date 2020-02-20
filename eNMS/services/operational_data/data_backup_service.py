from datetime import datetime
from flask_wtf import FlaskForm
from pathlib import Path
from re import M, sub
from sqlalchemy import Boolean, Float, ForeignKey, Integer
from wtforms import FieldList, FormField, HiddenField, StringField

from eNMS.database.dialect import Column, MutableList, LargeString, SmallString
from eNMS.forms.automation import NetmikoForm
from eNMS.models.automation import ConnectionService


class DataBackupService(ConnectionService):

    __tablename__ = "data_backup_service"
    pretty_name = "Netmiko Operational Data Backup"
    parent_type = "connection_service"
    id = Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    enable_mode = Column(Boolean, default=True)
    config_mode = Column(Boolean, default=False)
    driver = Column(SmallString)
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=10.0)
    global_delay_factor = Column(Float, default=1.0)
    configuration = Column(LargeString)
    operational_data = Column(MutableList)
    replacements = Column(MutableList)

    __mapper_args__ = {"polymorphic_identity": "data_backup_service"}

    def job(self, run, payload, device):
        path = Path.cwd() / "network_data" / device.name
        path.mkdir(parents=True, exist_ok=True)
        try:
            device.last_runtime = datetime.now()
            netmiko_connection = run.netmiko_connection(device)
            run.log("info", "Fetching Operational Data", device)
            for data in ("configuration", "operational_data"):
                value = run.sub(getattr(self, data), locals())
                if data == "configuration":
                    result = netmiko_connection.send_command(value)
                    for r in self.replacements:
                        result = sub(r["pattern"], r["replace_with"], result, flags=M)
                else:
                    result = f"\n\n".join(
                        f"{cmd['command']}\n"
                        + "\n".join(
                            f"{cmd['prefix']} - {line}" if cmd["prefix"] else line
                            for line in netmiko_connection.send_command(
                                cmd["command"]
                            ).splitlines()
                        )
                        for cmd in value
                    )
                setattr(device, data, result)
                with open(path / data, "w") as file:
                    file.write(result)
            device.last_status = "Success"
            device.last_duration = (
                f"{(datetime.now() - device.last_runtime).total_seconds()}s"
            )
            device.last_update = str(device.last_runtime)
            run.generate_yaml_file(path, device)
        except Exception as e:
            device.last_status = "Failure"
            device.last_failure = str(device.last_runtime)
            run.generate_yaml_file(path, device)
            return {"success": False, "result": str(e)}
        return {"success": True}


class ReplacementForm(FlaskForm):
    pattern = StringField("Pattern")
    replace_with = StringField("Replace With")


class OperationalDataForm(FlaskForm):
    command = StringField("Result of this Command stored as Operational Data")
    prefix = StringField("Label for this Command (Prefix)")


class DataBackupForm(NetmikoForm):
    form_type = HiddenField(default="data_backup_service")
    configuration = StringField("Result of this Command stored as Configuration")
    operational_data = FieldList(FormField(OperationalDataForm), min_entries=12)
    replacements = FieldList(FormField(ReplacementForm), min_entries=12)
    groups = {
        "Create Configuration File": {
            "commands": ["configuration"],
            "default": "expanded",
        },
        "Create Operational Data File": {
            "commands": ["operational_data"],
            "default": "expanded",
        },
        "Search Response & Replace": {
            "commands": ["replacements"],
            "default": "expanded",
        },
        **NetmikoForm.groups,
    }

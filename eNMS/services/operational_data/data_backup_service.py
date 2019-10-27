from datetime import datetime
from flask_wtf import FlaskForm
from pathlib import Path
from re import M, sub
from ruamel import yaml
from sqlalchemy import Boolean, Float, ForeignKey, Integer
from wtforms import FieldList, FormField, HiddenField, StringField

from eNMS.database.dialect import Column, MutableList, SmallString
from eNMS.database.functions import factory
from eNMS.forms.automation import NetmikoForm
from eNMS.models.automation import ConnectionService


class DataBackupService(ConnectionService):

    __tablename__ = "data_backup_service"
    pretty_name = "Operational Data Backup"
    id = Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    enable_mode = Column(Boolean, default=True)
    config_mode = Column(Boolean, default=False)
    driver = Column(SmallString)
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=10.0)
    global_delay_factor = Column(Float, default=1.0)
    categories = Column(MutableList)

    __mapper_args__ = {"polymorphic_identity": "data_backup_service"}

    def job(self, run, payload, device):
        path = Path.cwd() / "git" / "operational_data" / device.name
        path.mkdir(parents=True, exist_ok=True)
        try:
            device.last_runtime = datetime.now()
            netmiko_connection = run.netmiko_connection(device)
            run.log("info", "Fetching Operational Data", device)
            data = {}
            for category in self.categories:
                if not category["name"]:
                    continue
                command = run.sub(category["command"], locals())
                output = netmiko_connection.send_command(command)
                output = sub(
                    category["pattern"], category["replace_with"], output, flags=M
                )
                device.data[category["name"]] = output
                if category["name"].lower() == "configuration":
                    device.configuration = output
                factory(
                    "data",
                    device=device.id,
                    runtime=device.last_runtime,
                    duration=device.last_duration,
                    category=category["name"],
                    command=category["command"],
                    output=output,
                )
            device.last_status = "Success"
            device.last_duration = (
                f"{(datetime.now() - device.last_runtime).total_seconds()}s"
            )
            device.last_update = str(device.last_runtime)
            with open(path / "dataset.yml", "w") as file:
                yaml.dump(data, file, default_flow_style=False)
            for category, output in data.items():
                with open(path / device.name / category, "w") as file:
                    file.write(output)
            run.generate_yaml_file(path, device)
        except Exception as e:
            device.last_status = "Failure"
            device.last_failure = str(device.last_runtime)
            run.generate_yaml_file(path, device)
            return {"success": False, "result": str(e)}
        return {"success": True}


class CategoryForm(FlaskForm):
    name = StringField("Category")
    command = StringField("Command")
    pattern = StringField("Pattern")
    replace_with = StringField("Replace With")


class DataBackupForm(NetmikoForm):
    form_type = HiddenField(default="data_backup_service")
    categories = FieldList(FormField(CategoryForm), min_entries=10)
    groups = {
        "Main Parameters": {"commands": ["categories"], "default": "expanded"},
        **NetmikoForm.groups,
    }

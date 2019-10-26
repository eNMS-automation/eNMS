from datetime import datetime
from flask_wtf import FlaskForm
from pathlib import Path
from re import M, sub
from ruamel import yaml
from sqlalchemy import Boolean, Float, ForeignKey, Integer
from wtforms import FieldList, FormField, HiddenField, StringField
from wtforms.widgets import TextArea

from eNMS.database.dialect import Column, LargeString, MutableList, SmallString
from eNMS.database.functions import factory
from eNMS.forms.automation import NetmikoForm
from eNMS.forms.fields import SubstitutionField
from eNMS.models.automation import ConnectionService


class DatasetBackupService(ConnectionService):

    __tablename__ = "dataset_backup_service"
    pretty_name = "Dataset Backup"
    id = Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    enable_mode = Column(Boolean, default=True)
    config_mode = Column(Boolean, default=False)
    driver = Column(SmallString)
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=10.0)
    global_delay_factor = Column(Float, default=1.0)
    category = Column(MutableList)

    __mapper_args__ = {"polymorphic_identity": "dataset_backup_service"}

    def job(self, run, payload, device):
        try:
            commands = run.sub(run.commands, locals()).splitlines()
            device.last_runtime = datetime.now()
            path_device_data = Path.cwd() / "git" / "datasets" / device.name
            path_device_data.mkdir(parents=True, exist_ok=True)
            netmiko_connection = run.netmiko_connection(device)
            run.log("info", "Fetching Operational Data", device)
            data = {}
            for command in commands:
                result = netmiko_connection.send_command(command)
                for i in range(1, 4):
                    result = sub(
                        getattr(self, f"regex_pattern_{i}"),
                        getattr(self, f"regex_replace_{i}"),
                        result,
                        flags=M,
                    )
                data[command] = result
            device.last_status = "Success"
            device.last_duration = (
                f"{(datetime.now() - device.last_runtime).total_seconds()}s"
            )
            if device.dataset == data:
                return {"success": True, "result": "no change"}
            device.dataset = data
            device.last_update = str(device.last_runtime)
            factory(
                "dataset",
                device=device.id,
                runtime=device.last_runtime,
                duration=device.last_duration,
                data=data,
            )
            with open(path_device_data / "dataset.yml", "w") as file:
                yaml.dump(data, file, default_flow_style=False)
            run.generate_yaml_file(path_device_data, device)
        except Exception as e:
            device.last_status = "Failure"
            device.last_failure = str(device.last_runtime)
            run.generate_yaml_file(path_device_data, device)
            return {"success": False, "result": str(e)}
        return {"success": True, "result": f"Command: {command}"}


class CategoryForm(FlaskForm):
    category_name = StringField("Category Name")
    command = StringField("Command")
    pattern = StringField("Pattern")
    replace_with = StringField("Replace With")


class DatasetBackupForm(NetmikoForm):
    form_type = HiddenField(default="dataset_backup_service")
    category = FieldList(FormField(CategoryForm), min_entries=1)
    groups = {
        "Main Parameters": {"commands": ["category"], "default": "expanded"},
        **NetmikoForm.groups,
    }

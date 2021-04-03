from datetime import datetime
from flask_wtf import FlaskForm
from pathlib import Path
from re import M, sub
from sqlalchemy import Boolean, ForeignKey, Integer
from wtforms import FormField

from eNMS import app
from eNMS.database import db
from eNMS.forms import NapalmForm
from eNMS.fields import (
    HiddenField,
    SelectField,
    StringField,
    SelectMultipleField,
    FieldList,
)
from eNMS.models.automation import ConnectionService
from eNMS.variables import napalm_getters


class NapalmBackupService(ConnectionService):

    __tablename__ = "napalm_backup_service"
    pretty_name = "NAPALM Data Backup"
    parent_type = "connection_service"
    id = db.Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    driver = db.Column(db.SmallString)
    use_device_driver = db.Column(Boolean, default=True)
    timeout = db.Column(Integer, default=60)
    optional_args = db.Column(db.Dict)
    property = db.Column(db.SmallString)
    getters = db.Column(db.List)
    replacements = db.Column(db.List)

    __mapper_args__ = {"polymorphic_identity": "napalm_backup_service"}

    def job(self, run, device):
        path = Path.cwd() / "network_data" / device.name
        path.mkdir(parents=True, exist_ok=True)
        try:
            runtime = datetime.now()
            setattr(device, f"last_{self.property}_runtime", str(runtime))
            napalm_connection = run.napalm_connection(device)
            run.log("info", f"Fetching getters: {', '.join(run.getters)}", device)
            result = {}
            for getter in run.getters:
                try:
                    output = app.str_dict(getattr(napalm_connection, getter)())
                    for r in self.replacements:
                        output = sub(
                            r["pattern"],
                            r["replace_with"],
                            output,
                            flags=M,
                        )
                    result[getter] = output
                except Exception as exc:
                    result[getter] = f"{getter} failed because of {exc}"
            result = app.str_dict(result)
            setattr(device, self.property, result)
            with open(path / self.property, "w") as file:
                file.write(result)
            setattr(device, f"last_{self.property}_status", "Success")
            duration = f"{(datetime.now() - runtime).total_seconds()}s"
            setattr(device, f"last_{self.property}_duration", duration)
            setattr(device, f"last_{self.property}_update", str(runtime))
            run.update_configuration_properties(path, self.property, device)
        except Exception as exc:
            setattr(device, f"last_{self.property}_status", "Failure")
            setattr(device, f"last_{self.property}_failure", str(runtime))
            run.update_configuration_properties(path, self.property, device)
            return {"success": False, "result": str(exc)}
        return {"success": True}


class ReplacementForm(FlaskForm):
    pattern = StringField("Pattern")
    replace_with = StringField("Replace With")


class NapalmBackupForm(NapalmForm):
    form_type = HiddenField(default="napalm_backup_service")
    property = SelectField(
        "Configuration Property to Update",
        choices=list(app.configuration_properties.items()),
    )
    getters = SelectMultipleField(choices=napalm_getters)
    replacements = FieldList(FormField(ReplacementForm), min_entries=3)
    groups = {
        "Target Property and Getters": {
            "commands": ["property", "getters"],
            "default": "expanded",
        },
        "Search Response & Replace": {
            "commands": ["replacements"],
            "default": "expanded",
        },
        **NapalmForm.groups,
    }

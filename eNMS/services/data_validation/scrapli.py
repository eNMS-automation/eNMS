from sqlalchemy import Boolean, ForeignKey, Integer
from wtforms.widgets import TextArea

from eNMS import app
from eNMS.database import db
from eNMS.forms import choices
from eNMS.forms.fields import BooleanField, HiddenField, SelectField, StringField
from eNMS.forms.automation import ConnectionForm
from eNMS.models.automation import ConnectionService


class ScrapliService(ConnectionService):

    __tablename__ = "scrapli_service"
    pretty_name = "Scrapli Commands"
    parent_type = "connection_service"
    id = db.Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    commands = db.Column(db.LargeString)
    is_configuration = db.Column(Boolean)
    driver = db.Column(db.SmallString)
    transport = db.Column(db.SmallString, default="system")
    use_device_driver = db.Column(Boolean, default=True)

    __mapper_args__ = {"polymorphic_identity": "scrapli_service"}

    def job(self, run, payload, device):
        commands = run.sub(run.commands, locals()).splitlines()
        function = "send_configs" if run.is_configuration else "send_commands"
        result = getattr(run.scrapli_connection(device), function)(commands).result
        return {"commands": commands, "result": result}


class ScrapliForm(ConnectionForm):
    form_type = HiddenField(default="scrapli_service")
    commands = StringField(substitution=True, widget=TextArea(), render_kw={"rows": 5})
    is_configuration = BooleanField()
    driver = SelectField(choices=choices(app.SCRAPLI_DRIVERS))
    transport = SelectField(choices=choices(("system", "paramiko", "ssh2")))
    use_device_driver = BooleanField(default=True)
    groups = {
        "Main Parameters": {
            "commands": [
                "commands",
                "is_configuration",
                "driver",
                "transport",
                "use_device_driver",
            ],
            "default": "expanded",
        },
        **ConnectionForm.groups,
    }

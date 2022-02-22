from sqlalchemy import Boolean, ForeignKey, Integer, Float
from wtforms.widgets import TextArea

from eNMS.database import db
from eNMS.fields import BooleanField, HiddenField, SelectField, StringField, FloatField
from eNMS.forms import ConnectionForm
from eNMS.models.automation import ConnectionService
from eNMS.variables import vs


class ScrapliService(ConnectionService):

    __tablename__ = "scrapli_service"
    pretty_name = "Scrapli Commands"
    parent_type = "connection_service"
    id = db.Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    commands = db.Column(db.LargeString)
    is_configuration = db.Column(Boolean, default=False)
    use_device_driver = db.Column(Boolean, default=True)
    driver = db.Column(db.SmallString)
    transport = db.Column(db.SmallString, default="system")
    timeout_socket = db.Column(Float, default=15.0)
    timeout_transport = db.Column(Float, default=30.0)
    timeout_ops = db.Column(Float, default=30.0)

    __mapper_args__ = {"polymorphic_identity": "scrapli_service"}

    def job(self, run, device):
        commands = run.sub(run.commands, locals()).splitlines()
        function = "send_configs" if run.is_configuration else "send_commands"
        result = getattr(run.scrapli_connection(device), function)(commands).result
        return {"commands": commands, "result": result}


class ScrapliForm(ConnectionForm):
    form_type = HiddenField(default="scrapli_service")
    commands = StringField(substitution=True, widget=TextArea(), render_kw={"rows": 5})
    is_configuration = BooleanField()
    use_device_driver = BooleanField(default=True)
    driver = SelectField(choices=vs.dualize(vs.scrapli_drivers))
    transport = SelectField(choices=vs.dualize(("system", "paramiko", "ssh2")))
    timeout_socket = FloatField("Socket Timeout", default=15.0)
    timeout_transport = FloatField("Transport Timeout", default=30.0)
    timeout_ops = FloatField("Ops Timeout", default=30.0)
    groups = {
        "Main Parameters": {
            "commands": [
                "commands",
                "is_configuration",
                "use_device_driver",
                "driver",
                "transport",
                "timeout_socket",
                "timeout_transport",
                "timeout_ops",
            ],
            "default": "expanded",
        },
        **ConnectionForm.groups,
    }

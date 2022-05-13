from sqlalchemy import Boolean, ForeignKey, Integer, Float
from wtforms.widgets import TextArea

from eNMS.database import db
from eNMS.fields import BooleanField, HiddenField, StringField
from eNMS.forms import ScrapliForm
from eNMS.models.automation import ConnectionService


class ScrapliService(ConnectionService):

    __tablename__ = "scrapli_service"
    pretty_name = "Scrapli Commands"
    parent_type = "connection_service"
    id = db.Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    commands = db.Column(db.LargeString)
    is_configuration = db.Column(Boolean, default=False)
    results_as_list = db.Column(Boolean, default=True)
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
        run.log(
            "info",
            f"sending COMMANDS {commands} with Scrapli",
            device,
            logger="security",
        )
        multi_response = getattr(run.scrapli_connection(device), function)(commands)
        result = (
            [resp.result for resp in multi_response]
            if self.results_as_list
            else multi_response.result
        )
        return {"commands": commands, "result": result}


class ScrapliCommandsForm(ScrapliForm):
    form_type = HiddenField(default="scrapli_service")
    commands = StringField(substitution=True, widget=TextArea(), render_kw={"rows": 5})
    results_as_list = BooleanField("Results As List", default=True)
    groups = {
        "Main Parameters": {
            "commands": ["commands", "results_as_list"],
            "default": "expanded",
        },
        **ScrapliForm.groups,
    }

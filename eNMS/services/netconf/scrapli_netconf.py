from sqlalchemy import Boolean, ForeignKey, Integer
from wtforms.widgets import TextArea

from eNMS.database import db
from eNMS.fields import BooleanField, HiddenField, SelectField, StringField
from eNMS.forms import ConnectionForm
from eNMS.models.automation import ConnectionService
from eNMS.variables import vs


class ScrapliNetconfService(ConnectionService):

    __tablename__ = "scrapli_netconf_service"
    pretty_name = "Scrapli Netconf"
    parent_type = "connection_service"
    id = db.Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    command = db.Column(db.SmallString)
    filter_ = db.Column(db.LargeString)
    commit = db.Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "scrapli_netconf_service"}

    def job(self, run, device):
        commands = run.sub(run.commands, locals()).splitlines()
        function = "send_configs" if run.is_configuration else "send_commands"
        result = getattr(run.scrapli_connection(device), function)(commands).result
        return {"commands": commands, "result": result}


class ScrapliNetconfForm(ConnectionForm):
    form_type = HiddenField(default="scrapli_netconf_service")
    command = SelectField(
        choices=(
            ("get", "Get"),
            ("rpc", "RPC"),
            ("get_config", "Get Configuration"),
            ("edit_config", "Edit Configuration"),
            ("delete_config", "Delete Configuration"),
            ("commit", "Commit Configuration"),
            ("discard", "Discard Configuration"),
            ("lock", "Lock"),
            ("unlock", "Unlock"),
        )
    )
    target = SelectField(
        choices=(
            ("running", "Running Configuration"),
            ("startup", "Startup Configuration"),
            ("candidate", "Candidate Configuration"),
        )
    )
    filter_ = StringField(substitution=True, widget=TextArea(), render_kw={"rows": 5})
    commit = BooleanField("Commit Configuration")
    groups = {
        "Main Parameters": {
            "commands": ["command", "target", "filter"],
            "default": "expanded",
        },
        **ConnectionForm.groups,
    }

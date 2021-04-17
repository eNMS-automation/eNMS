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
    content = db.Column(db.LargeString)

    __mapper_args__ = {"polymorphic_identity": "scrapli_netconf_service"}

    def job(self, run, device):
        commands = run.sub(run.commands, locals()).splitlines()
        function = "send_configs" if run.is_configuration else "send_commands"
        result = getattr(run.scrapli_connection(device), function)(commands).result
        return {"commands": commands, "result": result}


class ScrapliNetconfForm(ConnectionForm):
    form_type = HiddenField(default="scrapli_netconf_service")
    command = StringField(substitution=True)
    content = StringField(substitution=True, widget=TextArea(), render_kw={"rows": 5})
    groups = {
        "Main Parameters": {
            "commands": [
                "command",
                "content"
            ],
            "default": "expanded",
        },
        **ConnectionForm.groups,
    }

from sqlalchemy import ForeignKey, Integer

from eNMS import app
from eNMS.database import db
from eNMS.forms import choices
from eNMS.forms.fields import HiddenField, SelectField, StringField
from eNMS.forms.automation import ConnectionForm
from eNMS.models.automation import ConnectionService


class ScrapliService(ConnectionService):

    __tablename__ = "scrapli_service"
    pretty_name = "Scrapli Commands"
    parent_type = "connection_service"
    id = db.Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    command = db.Column(db.LargeString)
    driver = db.Column(db.SmallString)
    use_device_driver = db.Column(Boolean, default=True)

    __mapper_args__ = {"polymorphic_identity": "scrapli_service"}

    def job(self, run, payload, device):
        command = run.sub(run.command, locals())
        connection = run.scrapli_connection(device)
        response = connection.send_command("show run")
        return {"command": command, "result": response.result}


class ScrapliForm(ConnectionForm):
    form_type = HiddenField(default="scrapli_service")
    command = StringField(substitution=True)
    driver = SelectField(choices=choices(app.SCRAPLI_DRIVERS))
    groups = {
        "Main Parameters": {"commands": ["command", "driver", "use_device_driver"], "default": "expanded"},
        **ConnectionForm.groups,
    }

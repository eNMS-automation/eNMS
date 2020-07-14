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

    __mapper_args__ = {"polymorphic_identity": "scrapli_service"}

    def job(self, run, payload, device):
        command = run.sub(run.command, locals())
        connection = run.scrapli_connection(device)
        return {"command": command, "result": "result"}


class ScrapliForm(ConnectionForm):
    form_type = HiddenField(default="scrapli_service")
    command = StringField(substitution=True)
    driver = SelectField(choices=choices(app.SCRAPLI_DRIVERS))
    groups = {
        "Main Parameters": {"commands": ["command", "driver"], "default": "expanded"},
        **ConnectionForm.groups,
    }

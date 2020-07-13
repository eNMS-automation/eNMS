from sqlalchemy import Boolean, ForeignKey, Integer

from eNMS.database import db
from eNMS.forms.fields import HiddenField, StringField
from eNMS.forms.automation import ConnectionForm
from eNMS.models.automation import ConnectionService


class NetmikoValidationService(ConnectionService):

    __tablename__ = "scrapli_service"
    pretty_name = "Scrapli Commands"
    parent_type = "connection_service"
    id = db.Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    command = db.Column(db.LargeString)
    driver = db.Column(db.SmallString)
    use_device_driver = db.Column(Boolean, default=True)
    fast_cli = db.Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "scrapli_service"}

    def job(self, run, payload, device):
        command = run.sub(run.command, locals())
        connection = run.scrapli_connection(device)
        return {"command": command, "result": "result"}


class NetmikoValidationForm(ConnectionForm):
    form_type = HiddenField(default="scrapli_service")
    command = StringField(substitution=True)
    groups = {
        "Main Parameters": {"commands": ["command"], "default": "expanded"},
        **ConnectionForm.groups,
    }

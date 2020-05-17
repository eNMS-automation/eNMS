from sqlalchemy import Boolean, ForeignKey, Integer
from wtforms.widgets import TextArea

from eNMS.database import db
from eNMS.forms.fields import HiddenField, SelectField, StringField
from eNMS.forms.automation import NapalmForm
from eNMS.models.automation import ConnectionService


class NapalmConfigurationService(ConnectionService):

    __tablename__ = "napalm_configuration_service"
    pretty_name = "NAPALM Configuration"
    parent_type = "connection_service"
    id = db.Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    action = db.Column(db.SmallString)
    content = db.Column(db.LargeString)
    driver = db.Column(db.SmallString)
    use_device_driver = db.Column(Boolean, default=True)
    timeout = db.Column(Integer, default=60)
    optional_args = db.Column(db.Dict)

    __mapper_args__ = {"polymorphic_identity": "napalm_configuration_service"}

    def job(self, run, payload, device):
        napalm_connection = run.napalm_connection(device)
        run.log(
            "info", "Pushing Configuration with NAPALM", device, logger="security",
        )
        config = "\n".join(run.sub(run.content, locals()).splitlines())
        getattr(napalm_connection, run.action)(config=config)
        napalm_connection.commit_config()
        return {"success": True, "result": f"Config push ({config})"}


class NapalmConfigurationForm(NapalmForm):
    form_type = HiddenField(default="napalm_configuration_service")
    action = SelectField(
        choices=(
            ("load_merge_candidate", "Load merge"),
            ("load_replace_candidate", "Load replace"),
        )
    )
    content = StringField(widget=TextArea(), render_kw={"rows": 5}, substitution=True)
    groups = {
        "Main Parameters": {"commands": ["action", "content"], "default": "expanded"},
        **NapalmForm.groups,
    }

from requests import post
from sqlalchemy import ForeignKey, Integer
from wtforms.widgets import TextArea

from eNMS.database import db
from eNMS.forms import ServiceForm
from eNMS.fields import HiddenField, StringField
from eNMS.models.automation import Service
from eNMS.variables import vs


class MattermostNotificationService(Service):
    __tablename__ = "mattermost_notification_service"
    pretty_name = "Mattermost Notification"
    id = db.Column(Integer, ForeignKey("service.id"), primary_key=True)
    channel = db.Column(db.SmallString)
    body = db.Column(db.LargeString)

    __mapper_args__ = {"polymorphic_identity": "mattermost_notification_service"}

    def job(self, run, device=None):
        channel = run.sub(run.channel, locals()) or vs.settings["mattermost"]["channel"]
        run.log("info", f"Sending MATTERMOST notification on {channel}", device)
        result = post(
            vs.settings["mattermost"]["url"],
            verify=vs.settings["mattermost"]["verify_certificate"],
            json={"channel": channel, "text": run.sub(run.body, locals())},
        )
        return {"success": True, "result": str(result)}


class MattermostNotificationForm(ServiceForm):
    form_type = HiddenField(default="mattermost_notification_service")
    channel = StringField(substitution=True)
    body = StringField(widget=TextArea(), render_kw={"rows": 5}, substitution=True)

from requests import post
from sqlalchemy import ForeignKey, Integer
from wtforms.widgets import TextArea

from eNMS import app
from eNMS.database import db
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import HiddenField, StringField
from eNMS.models.automation import Service


class MattermostNotificationService(Service):

    __tablename__ = "mattermost_notification_service"
    pretty_name = "Mattermost Notification"
    id = db.Column(Integer, ForeignKey("service.id"), primary_key=True)
    channel = db.Column(db.SmallString)
    body = db.Column(db.LargeString)

    __mapper_args__ = {"polymorphic_identity": "mattermost_notification_service"}

    def job(self, run, payload, device=None):
        channel = (
            run.sub(run.channel, locals()) or app.settings["mattermost"]["channel"]
        )
        run.log("info", f"Sending MATTERMOST notification on {channel}", device)
        result = post(
            app.settings["mattermost"]["url"],
            verify=app.settings["mattermost"]["verify_certificate"],
            json={"channel": channel, "text": run.sub(run.body, locals())},
        )
        return {"success": True, "result": str(result)}


class MattermostNotificationForm(ServiceForm):
    form_type = HiddenField(default="mattermost_notification_service")
    channel = StringField(substitution=True)
    body = StringField(widget=TextArea(), render_kw={"rows": 5}, substitution=True)

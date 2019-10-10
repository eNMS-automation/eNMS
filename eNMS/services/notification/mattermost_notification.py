from json import dumps
from requests import post
from sqlalchemy import ForeignKey, Integer
from wtforms import HiddenField
from wtforms.widgets import TextArea

from eNMS import app
from eNMS.database.dialect import Column, LargeString, SmallString
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.models.automation import Service


class MattermostNotificationService(Service):

    __tablename__ = "mattermost_notification_service"
    pretty_name = "Mattermost Notification"

    id = Column(Integer, ForeignKey("service.id"), primary_key=True)
    channel = Column(SmallString)
    body = Column(LargeString, default="")

    __mapper_args__ = {"polymorphic_identity": "mattermost_notification_service"}

    def job(self, run, payload, device=None):
        channel = run.sub(run.channel, locals()) or app.mattermost_channel
        run.log("info", f"Sending MATTERMOST notification on {channel}", device)
        result = post(
            app.mattermost_url,
            verify=app.mattermost_verify_certificate,
            data=dumps({"channel": channel, "text": run.sub(run.body, locals())}),
        )
        return {"success": True, "result": str(result)}


class MattermostNotificationForm(ServiceForm):
    form_type = HiddenField(default="mattermost_notification_service")
    channel = SubstitutionField()
    body = SubstitutionField(widget=TextArea(), render_kw={"rows": 5})

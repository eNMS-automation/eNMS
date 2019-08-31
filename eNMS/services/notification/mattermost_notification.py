from json import dumps
from requests import post
from sqlalchemy import Boolean, ForeignKey, Integer
from typing import Optional
from wtforms import HiddenField
from wtforms.widgets import TextArea

from eNMS import app
from eNMS.database.dialect import Column, LargeString, SmallString
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.models.automation import Service
from eNMS.models.execution import Run
from eNMS.models.inventory import Device


class MattermostNotificationService(Service):

    __tablename__ = "MattermostNotificationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = Column(Boolean, default=False)
    channel = Column(SmallString)
    body = Column(LargeString, default="")

    __mapper_args__ = {"polymorphic_identity": "MattermostNotificationService"}

    def job(self, run: "Run", payload: dict, device: Optional[Device] = None) -> dict:
        channel = run.sub(run.channel, locals()) or app.mattermost_channel
        run.log("info", f"Sending Mattermost notification on {channel}")
        result = post(
            app.mattermost_url,
            verify=app.mattermost_verify_certificate,
            data=dumps({"channel": channel, "text": run.sub(run.body, locals())}),
        )
        return {"success": True, "result": str(result)}


class MattermostNotificationForm(ServiceForm):
    form_type = HiddenField(default="MattermostNotificationService")
    channel = SubstitutionField()
    body = SubstitutionField(widget=TextArea(), render_kw={"rows": 5})

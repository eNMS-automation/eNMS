from json import dumps
from requests import post
from sqlalchemy import Column, ForeignKey, Integer, String, Text
from wtforms import HiddenField, StringField
from wtforms.widgets import TextArea

from eNMS.database import LARGE_STRING_LENGTH, get_one, SMALL_STRING_LENGTH
from eNMS.forms import metaform
from eNMS.forms.automation import ServiceForm
from eNMS.models import register_class
from eNMS.models.automation import Service


class MattermostNotificationService(Service, metaclass=register_class):

    __tablename__ = "MattermostNotificationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    channel = Column(String(SMALL_STRING_LENGTH), default="")
    body = Column(Text(LARGE_STRING_LENGTH), default="")

    __mapper_args__ = {"polymorphic_identity": "MattermostNotificationService"}

    def job(self, _) -> dict:
        parameters = get_one("Parameters")
        channel = self.channel or parameters.mattermost_channel
        self.logs.append(f"Sending Mattermost notification on {channel}")
        result = post(
            parameters.mattermost_url,
            verify=parameters.mattermost_verify_certificate,
            data=dumps({"channel": channel, "text": self.body}),
        )
        return {"success": True, "result": str(result)}


class MattermostNotificationForm(ServiceForm, metaclass=metaform):
    form_type = HiddenField(default="MattermostNotificationService")
    channel = StringField()
    body = StringField(widget=TextArea(), render_kw={"rows": 5})

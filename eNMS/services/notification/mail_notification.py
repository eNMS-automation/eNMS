from sqlalchemy import ForeignKey, Integer
from wtforms.widgets import TextArea

from eNMS import app
from eNMS.database import db
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import HiddenField, StringField
from eNMS.models.automation import Service


class MailNotificationService(Service):

    __tablename__ = "mail_notification_service"
    pretty_name = "Mail Notification"
    id = db.Column(Integer, ForeignKey("service.id"), primary_key=True)
    title = db.Column(db.SmallString)
    sender = db.Column(db.SmallString)
    recipients = db.Column(db.SmallString)
    replier = db.Column(db.SmallString, default="")
    body = db.Column(db.LargeString)

    __mapper_args__ = {"polymorphic_identity": "mail_notification_service"}

    def job(self, run, payload, device=None):
        app.send_email(
            run.sub(run.title, locals()),
            run.sub(run.body, locals()),
            sender=run.sender,
            recipients=run.recipients,
            reply_to=run.replier,
        )
        return {"success": True, "result": {}}


class MailNotificationForm(ServiceForm):
    form_type = HiddenField(default="mail_notification_service")
    title = StringField(substitution=True)
    sender = StringField()
    recipients = StringField()
    replier = StringField("Reply-to Address")
    body = StringField(widget=TextArea(), render_kw={"rows": 5}, substitution=True)

    def validate(self):
        valid_form = super().validate()
        for field in ("title", "sender", "recipients", "body"):
            if not getattr(self, field).data:
                getattr(self, field).errors.append(f"{field.capitalize()} is missing.")
                valid_form = False
        return valid_form

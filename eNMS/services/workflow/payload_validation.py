from sqlalchemy import ForeignKey, Integer

from eNMS.database import db
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import HiddenField, StringField
from eNMS.models.automation import Service


class PayloadValidationService(Service):

    __tablename__ = "payload_validation_service"
    pretty_name = "Payload Validation"
    id = db.Column(Integer, ForeignKey("service.id"), primary_key=True)
    query = db.Column(db.SmallString)

    __mapper_args__ = {"polymorphic_identity": "payload_validation_service"}

    def job(self, run, payload, device=None):
        return {"query": run.query, "result": run.eval(run.query, **locals())[0]}


class PayloadValidationForm(ServiceForm):
    form_type = HiddenField(default="payload_validation_service")
    query = StringField("Python Query", python=True)

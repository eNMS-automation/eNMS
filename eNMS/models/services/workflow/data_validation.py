from sqlalchemy import ForeignKey, Integer

from eNMS.database import db
from eNMS.forms import ServiceForm
from eNMS.fields import HiddenField, StringField
from eNMS.models.automation import Service


class DataValidationService(Service):
    __tablename__ = "data_validation_service"
    pretty_name = "Data Validation"
    id = db.Column(Integer, ForeignKey("service.id"), primary_key=True)
    query = db.Column(db.SmallString)

    __mapper_args__ = {"polymorphic_identity": "data_validation_service"}

    def job(self, run, device=None):
        return {"query": run.query, "result": run.eval(run.query, **locals())[0]}


class DataValidationForm(ServiceForm):
    form_type = HiddenField(default="data_validation_service")
    query = StringField("Python Query", python=True)

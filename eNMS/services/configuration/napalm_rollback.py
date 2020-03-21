from sqlalchemy import Boolean, ForeignKey, Integer

from eNMS.database import db
from eNMS.forms.automation import NapalmForm
from eNMS.forms.fields import HiddenField
from eNMS.models.automation import ConnectionService


class NapalmRollbackService(ConnectionService):

    __tablename__ = "napalm_rollback_service"
    pretty_name = "NAPALM Rollback"
    parent_type = "connection_service"
    id = db.Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    driver = db.Column(db.SmallString)
    use_device_driver = db.Column(Boolean, default=True)
    timeout = db.Column(Integer, default=60)
    optional_args = db.Column(db.Dict)

    __mapper_args__ = {"polymorphic_identity": "napalm_rollback_service"}

    def job(self, run, payload, device):
        napalm_connection = run.napalm_connection(device)
        run.log("info", "Configuration Rollback with NAPALM", device)
        napalm_connection.rollback()
        return {"success": True, "result": "Rollback successful"}


class NapalmRollbackForm(NapalmForm):
    form_type = HiddenField(default="napalm_rollback_service")

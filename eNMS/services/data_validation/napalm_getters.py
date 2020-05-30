from sqlalchemy import Boolean, ForeignKey, Integer

from eNMS import app
from eNMS.database import db
from eNMS.forms.automation import NapalmForm
from eNMS.forms.fields import HiddenField, SelectMultipleField
from eNMS.models.automation import ConnectionService


class NapalmGettersService(ConnectionService):

    __tablename__ = "napalm_getters_service"
    pretty_name = "NAPALM getters"
    parent_type = "connection_service"
    id = db.Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    driver = db.Column(db.SmallString)
    use_device_driver = db.Column(Boolean, default=True)
    timeout = db.Column(Integer, default=60)
    getters = db.Column(db.List)
    optional_args = db.Column(db.Dict)

    __mapper_args__ = {"polymorphic_identity": "napalm_getters_service"}

    def job(self, run, payload, device):
        napalm_connection, result = run.napalm_connection(device), {}
        run.log(
            "info",
            f"Fetching NAPALM getters ({', '.join(run.getters)})",
            device,
            logger="security",
        )
        for getter in run.getters:
            try:
                result[getter] = getattr(napalm_connection, getter)()
            except Exception as exc:
                result[getter] = f"{getter} failed because of {exc}"
        return {"result": result}


class NapalmGettersForm(NapalmForm):
    form_type = HiddenField(default="napalm_getters_service")
    getters = SelectMultipleField(choices=app.NAPALM_GETTERS)
    groups = {
        "Main Parameters": {"commands": ["getters"], "default": "expanded"},
        **NapalmForm.groups,
    }

from sqlalchemy import ForeignKey, Integer

from eNMS.database import db
from eNMS.forms import NapalmForm
from eNMS.fields import HiddenField, SelectMultipleField
from eNMS.models.automation import ConnectionService
from eNMS.variables import vs


class NapalmGettersService(ConnectionService):
    __tablename__ = "napalm_getters_service"
    pretty_name = "NAPALM getters"
    parent_type = "connection_service"
    id = db.Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    driver = db.Column(db.SmallString)
    timeout = db.Column(Integer, default=60)
    getters = db.Column(db.List)
    optional_args = db.Column(db.Dict)

    __mapper_args__ = {"polymorphic_identity": "napalm_getters_service"}

    def job(self, run, device):
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
    getters = SelectMultipleField(choices=vs.automation["napalm"]["getters"])
    groups = {
        "Main Parameters": {"commands": ["getters"], "default": "expanded"},
        **NapalmForm.groups,
    }

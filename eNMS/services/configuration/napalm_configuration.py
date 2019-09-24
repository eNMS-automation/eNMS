from sqlalchemy import Boolean, ForeignKey, Integer
from wtforms import HiddenField, SelectField
from wtforms.widgets import TextArea

from eNMS.database.dialect import Column, LargeString, MutableDict, SmallString
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.forms.services import NapalmForm
from eNMS.models.automation import Service
from eNMS.models.execution import Run
from eNMS.models.inventory import Device


class NapalmConfigurationService(Service):

    __tablename__ = "napalm_configuration_service"

    id = Column(Integer, ForeignKey("service.id"), primary_key=True)
    has_targets = True
    action = Column(SmallString)
    content = Column(LargeString, default="")
    driver = Column(SmallString)
    use_device_driver = Column(Boolean, default=True)
    optional_args = Column(MutableDict)

    __mapper_args__ = {"polymorphic_identity": "napalm_configuration_service"}

    def job(self, run: "Run", payload, device: Device) -> dict:
        napalm_connection = run.napalm_connection(device)
        run.log("info", f"Pushing configuration on {device.name} (Napalm)")
        config = "\n".join(run.sub(run.content, locals()).splitlines())
        getattr(napalm_connection, run.action)(config=config)
        napalm_connection.commit_config()
        return {"success": True, "result": f"Config push ({config})"}


class NapalmConfigurationForm(ServiceForm, NapalmForm):
    form_type = HiddenField(default="napalm_configuration_service")
    action = SelectField(
        choices=(
            ("load_merge_candidate", "Load merge"),
            ("load_replace_candidate", "Load replace"),
        )
    )
    content = SubstitutionField(widget=TextArea(), render_kw={"rows": 5})

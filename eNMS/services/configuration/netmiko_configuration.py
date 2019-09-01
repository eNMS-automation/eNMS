from sqlalchemy import Boolean, Float, ForeignKey, Integer
from wtforms import BooleanField, HiddenField, StringField
from wtforms.widgets import TextArea

from eNMS.database.dialect import Column, LargeString, SmallString
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.forms.services import NetmikoForm
from eNMS.models.automation import Service
from eNMS.models.execution import Run
from eNMS.models.inventory import Device


class NetmikoConfigurationService(Service):

    __tablename__ = "NetmikoConfigurationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    content = Column(LargeString, default="")
    privileged_mode = Column(Boolean, default=False)
    driver = Column(SmallString)
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=1.0)
    delay_factor = Column(Float, default=1.0)
    global_delay_factor = Column(Float, default=1.0)
    commit_configuration = Column(Boolean, default=False)
    exit_config_mode = Column(Boolean, default=True)
    strip_prompt = Column(Boolean, default=False)
    strip_command = Column(Boolean, default=False)
    config_mode_command = Column(SmallString)

    __mapper_args__ = {"polymorphic_identity": "NetmikoConfigurationService"}

    def job(self, run: "Run", payload: dict, device: Device) -> dict:
        netmiko_connection = run.netmiko_connection(device)
        config = run.sub(run.content, locals())
        run.log("info", f"Pushing configuration on {device.name} (Netmiko)")
        netmiko_connection.send_config_set(
            config.splitlines(),
            delay_factor=run.delay_factor,
            exit_config_mode=run.exit_config_mode,
            strip_prompt=run.strip_prompt,
            strip_command=run.strip_command,
            config_mode_command=run.config_mode_command,
        )
        if run.commit_configuration:
            netmiko_connection.commit()
        return {"success": True, "result": f"configuration OK {config}"}


class NetmikoConfigurationForm(ServiceForm, NetmikoForm):
    form_type = HiddenField(default="NetmikoConfigurationService")
    content = SubstitutionField(widget=TextArea(), render_kw={"rows": 5})
    commit_configuration = BooleanField()
    exit_config_mode = BooleanField(default=True)
    strip_prompt = BooleanField()
    strip_command = BooleanField()
    config_mode_command = StringField()
    groups = {
        "Main Parameters": {
            "commands": [
                "content",
                "commit_configuration",
                "exit_config_mode",
                "config_mode_command",
            ],
            "default": "expanded",
        },
        "Netmiko Parameters": NetmikoForm.group,
        "Advanced Netmiko Parameters": {
            "commands": ["strip_prompt", "strip_command"],
            "default": "hidden",
        },
    }

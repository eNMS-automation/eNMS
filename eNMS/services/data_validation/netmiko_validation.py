from sqlalchemy import Boolean, Float, ForeignKey, Integer
from traceback import format_exc

from eNMS.database import db
from eNMS.forms.fields import BooleanField, HiddenField, StringField
from eNMS.forms.automation import NetmikoForm
from eNMS.models.automation import ConnectionService


class NetmikoValidationService(ConnectionService):

    __tablename__ = "netmiko_validation_service"
    pretty_name = "Netmiko Validation"
    parent_type = "connection_service"
    id = db.Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    enable_mode = db.Column(Boolean, default=True)
    config_mode = db.Column(Boolean, default=False)
    command = db.Column(db.LargeString)
    driver = db.Column(db.SmallString)
    use_device_driver = db.Column(Boolean, default=True)
    fast_cli = db.Column(Boolean, default=False)
    timeout = db.Column(Float, default=10.0)
    delay_factor = db.Column(Float, default=1.0)
    global_delay_factor = db.Column(Float, default=1.0)
    expect_string = db.Column(db.SmallString)
    auto_find_prompt = db.Column(Boolean, default=True)
    strip_prompt = db.Column(Boolean, default=True)
    strip_command = db.Column(Boolean, default=True)
    use_genie = db.Column(Boolean, default=False)
    jump_on_connect = db.Column(Boolean, default=False)
    jump_command = db.Column(db.SmallString)
    jump_username = db.Column(db.SmallString)
    jump_password = db.Column(db.SmallString)
    exit_command = db.Column(db.SmallString)
    expect_username_prompt = db.Column(db.SmallString)
    expect_password_prompt = db.Column(db.SmallString)
    expect_prompt = db.Column(db.SmallString)

    __mapper_args__ = {"polymorphic_identity": "netmiko_validation_service"}

    def job(self, run, payload, device):
        command = run.sub(run.command, locals())
        netmiko_connection = run.netmiko_connection(device)
        try:
            prompt = run.enter_remote_device(netmiko_connection, device)
            netmiko_connection.session_log.truncate(0)
            run.log(
                "info",
                f"sending COMMAND '{command}' with Netmiko",
                device,
                logger="security",
            )
            result = netmiko_connection.send_command(
                command,
                delay_factor=run.delay_factor,
                expect_string=run.sub(run.expect_string, locals()) or None,
                auto_find_prompt=run.auto_find_prompt,
                strip_prompt=run.strip_prompt,
                strip_command=run.strip_command,
                use_genie=self.use_genie,
            )
            run.exit_remote_device(netmiko_connection, prompt, device)
        except Exception:
            result = netmiko_connection.session_log.getvalue().decode().lstrip("\u0000")
            return {
                "command": command,
                "error": format_exc(),
                "result": result,
                "success": False,
            }
        return {"command": command, "result": result}


class NetmikoValidationForm(NetmikoForm):
    form_type = HiddenField(default="netmiko_validation_service")
    command = StringField(substitution=True)
    expect_string = StringField(
        substitution=True, render_kw={"help": "netmiko/expect_string"}
    )
    auto_find_prompt = BooleanField(
        default=True, render_kw={"help": "netmiko/auto_find_prompt"}
    )
    strip_prompt = BooleanField(
        default=True, render_kw={"help": "netmiko/strip_prompt"}
    )
    strip_command = BooleanField(
        default=True, render_kw={"help": "netmiko/strip_command"}
    )
    use_genie = BooleanField(default=False)
    groups = {
        "Main Parameters": {"commands": ["command"], "default": "expanded"},
        **NetmikoForm.groups,
        "Advanced Netmiko Parameters": {
            "commands": [
                "expect_string",
                "auto_find_prompt",
                "strip_prompt",
                "strip_command",
                "use_genie",
            ],
            "default": "hidden",
        },
    }

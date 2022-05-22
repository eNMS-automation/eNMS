from sqlalchemy import Boolean, Float, ForeignKey, Integer
from traceback import format_exc
from wtforms.widgets import TextArea

from eNMS.database import db
from eNMS.fields import BooleanField, HiddenField, StringField
from eNMS.forms import NetmikoForm
from eNMS.models.automation import ConnectionService


class NetmikoValidationService(ConnectionService):

    __tablename__ = "netmiko_validation_service"
    pretty_name = "Netmiko Validation"
    parent_type = "connection_service"
    id = db.Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    enable_mode = db.Column(Boolean, default=True)
    config_mode = db.Column(Boolean, default=False)
    command = db.Column(db.LargeString)
    results_as_list = db.Column(Boolean, default=False)
    driver = db.Column(db.SmallString)
    use_device_driver = db.Column(Boolean, default=True)
    use_textfsm = db.Column(Boolean, default=False)
    fast_cli = db.Column(Boolean, default=False)
    timeout = db.Column(Float, default=10.0)
    delay_factor = db.Column(Float, default=1.0)
    global_delay_factor = db.Column(Float, default=1.0)
    expect_string = db.Column(db.SmallString)
    config_mode_command = db.Column(db.SmallString)
    auto_find_prompt = db.Column(Boolean, default=True)
    strip_prompt = db.Column(Boolean, default=True)
    strip_command = db.Column(Boolean, default=True)
    jump_on_connect = db.Column(Boolean, default=False)
    jump_command = db.Column(db.SmallString)
    jump_username = db.Column(db.SmallString)
    jump_password = db.Column(db.SmallString)
    exit_command = db.Column(db.SmallString)
    expect_username_prompt = db.Column(db.SmallString)
    expect_password_prompt = db.Column(db.SmallString)
    expect_prompt = db.Column(db.SmallString)

    __mapper_args__ = {"polymorphic_identity": "netmiko_validation_service"}

    def job(self, run, device):
        commands = run.sub(run.command, locals())
        log_command = run.command if "get_credential" in run.command else commands
        netmiko_connection = run.netmiko_connection(device)
        try:
            prompt = run.enter_remote_device(netmiko_connection, device)
            netmiko_connection.session_log.truncate(0)
            run.log(
                "info",
                f"sending COMMAND '{log_command}' with Netmiko",
                device,
                logger="security",
            )
            result = [
                netmiko_connection.send_command(
                    command,
                    use_textfsm=run.use_textfsm,
                    delay_factor=run.delay_factor,
                    expect_string=run.sub(run.expect_string, locals()) or None,
                    auto_find_prompt=run.auto_find_prompt,
                    strip_prompt=run.strip_prompt,
                    strip_command=run.strip_command,
                )
                for command in commands.splitlines()
            ]
            if not run.results_as_list:
                result = "\n".join(result)
            run.exit_remote_device(netmiko_connection, prompt, device)
        except Exception:
            result = netmiko_connection.session_log.getvalue().decode().lstrip("\u0000")
            return {
                "command": log_command,
                "error": format_exc(),
                "result": result,
                "success": False,
            }
        return {"command": log_command, "result": result}


class NetmikoValidationForm(NetmikoForm):
    form_type = HiddenField(default="netmiko_validation_service")
    command = StringField(substitution=True, widget=TextArea(), render_kw={"rows": 5})
    results_as_list = BooleanField("Results As List")
    use_textfsm = BooleanField("Use TextFSM", default=False)
    expect_string = StringField(substitution=True, help="netmiko/expect_string")
    config_mode_command = StringField(help="netmiko/config_mode_command")
    auto_find_prompt = BooleanField(default=True, help="netmiko/auto_find_prompt")
    strip_prompt = BooleanField(default=True, help="netmiko/strip_prompt")
    strip_command = BooleanField(default=True, help="netmiko/strip_command")
    groups = {
        "Main Parameters": {
            "commands": ["command", "results_as_list"],
            "default": "expanded",
        },
        **NetmikoForm.groups,
        "Advanced Netmiko Parameters": {
            "commands": [
                "use_textfsm",
                "expect_string",
                "config_mode_command",
                "auto_find_prompt",
                "strip_prompt",
                "strip_command",
            ],
            "default": "hidden",
        },
    }

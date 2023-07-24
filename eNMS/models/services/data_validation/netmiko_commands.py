from jinja2 import Template
from sqlalchemy import Boolean, Float, ForeignKey, Integer
from traceback import format_exc
from wtforms.widgets import TextArea

from eNMS.database import db
from eNMS.fields import BooleanField, HiddenField, StringField
from eNMS.forms import NetmikoForm
from eNMS.models.automation import ConnectionService


class NetmikoValidationService(ConnectionService):
    __tablename__ = "netmiko_commands_service"
    pretty_name = "Netmiko Commands"
    parent_type = "connection_service"
    id = db.Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    enable_mode = db.Column(Boolean, default=True)
    config_mode = db.Column(Boolean, default=False)
    commands = db.Column(db.LargeString)
    jinja2_template = db.Column(Boolean, default=False)
    results_as_list = db.Column(Boolean, default=False)
    driver = db.Column(db.SmallString)
    use_textfsm = db.Column(Boolean, default=False)
    use_genie = db.Column(Boolean, default=False)
    read_timeout = db.Column(Float, default=10.0)
    conn_timeout = db.Column(Float, default=10.0)
    auth_timeout = db.Column(Float, default=0.0)
    banner_timeout = db.Column(Float, default=15.0)
    fast_cli = db.Column(Boolean, default=False)
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

    __mapper_args__ = {"polymorphic_identity": "netmiko_commands_service"}

    def job(self, run, device):
        local_variables = locals()
        if self.jinja2_template:
            variables = {**local_variables, **run.global_variables()}
            commands = Template(run.commands).render(variables)
        else:
            commands = run.sub(run.commands, local_variables)
        netmiko_connection = run.netmiko_connection(device)
        try:
            prompt = run.enter_remote_device(netmiko_connection, device)
            netmiko_connection.session_log.session_log.truncate(0)
            run.log(
                "info",
                f"sending COMMAND '{commands}' with Netmiko",
                device,
                logger="security",
            )
            commands = commands.splitlines()
            result = [
                netmiko_connection.send_command(
                    command,
                    use_textfsm=run.use_textfsm,
                    use_genie=run.use_genie,
                    expect_string=run.sub(run.expect_string, local_variables) or None,
                    auto_find_prompt=run.auto_find_prompt,
                    read_timeout=run.read_timeout,
                    strip_prompt=run.strip_prompt,
                    strip_command=run.strip_command,
                )
                for command in commands
            ]
            if len(result) == 1:
                (result,) = result
            elif not run.results_as_list:
                for index in range(len(result)):
                    prefix = "{}COMMAND :".format("\n" if index else "")
                    result[index] = prefix + commands[index] + "\n\n" + result[index]
                result = "\n".join(map(str, result))
            run.exit_remote_device(netmiko_connection, prompt, device)
        except Exception:
            result = (
                netmiko_connection.session_log.session_log.getvalue()
                .decode()
                .lstrip("\u0000")
            )
            return {
                "commands": commands,
                "error": format_exc(),
                "result": result,
                "success": False,
            }
        return {"commands": commands, "result": result}


class NetmikoValidationForm(NetmikoForm):
    form_type = HiddenField(default="netmiko_commands_service")
    commands = StringField(substitution=True, widget=TextArea(), render_kw={"rows": 5})
    jinja2_template = BooleanField(
        "Interpret Commands as Jinja2 Template",
        default=False,
        help="common/commands_jinja",
    )
    results_as_list = BooleanField("Results As List", default=False)
    use_textfsm = BooleanField("Use TextFSM", default=False)
    use_genie = BooleanField("Use Genie / PyATS", default=False)
    auto_find_prompt = BooleanField(default=True, help="netmiko/auto_find_prompt")
    expect_string = StringField(substitution=True, help="netmiko/expect_string")
    config_mode_command = StringField(help="netmiko/config_mode_command")
    strip_prompt = BooleanField(default=True, help="netmiko/strip_prompt")
    strip_command = BooleanField(default=True, help="netmiko/strip_command")
    groups = {
        "Main Parameters": {
            "commands": ["commands", "jinja2_template", "results_as_list"],
            "default": "expanded",
        },
        **NetmikoForm.groups,
        "Advanced Netmiko Parameters": {
            "commands": [
                "use_textfsm",
                "use_genie",
                "auto_find_prompt",
                "expect_string",
                "config_mode_command",
                "strip_prompt",
                "strip_command",
            ],
            "default": "hidden",
        },
    }

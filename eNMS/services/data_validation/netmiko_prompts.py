from sqlalchemy import Boolean, Float, ForeignKey, Integer
from traceback import format_exc

from eNMS.database import db
from eNMS.forms.fields import HiddenField, StringField
from eNMS.forms.automation import NetmikoForm
from eNMS.models.automation import ConnectionService


class NetmikoPromptsService(ConnectionService):

    __tablename__ = "netmiko_prompts_service"
    pretty_name = "Netmiko Prompts"
    parent_type = "connection_service"
    id = db.Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    enable_mode = db.Column(Boolean, default=True)
    config_mode = db.Column(Boolean, default=False)
    command = db.Column(db.SmallString)
    confirmation1 = db.Column(db.LargeString)
    response1 = db.Column(db.SmallString)
    confirmation2 = db.Column(db.LargeString)
    response2 = db.Column(db.SmallString)
    confirmation3 = db.Column(db.LargeString)
    response3 = db.Column(db.SmallString)
    driver = db.Column(db.SmallString)
    use_device_driver = db.Column(Boolean, default=True)
    fast_cli = db.Column(Boolean, default=False)
    timeout = db.Column(Integer, default=10.0)
    delay_factor = db.Column(Float, default=1.0)
    global_delay_factor = db.Column(Float, default=1.0)
    jump_on_connect = db.Column(Boolean, default=False)
    jump_command = db.Column(db.SmallString)
    jump_username = db.Column(db.SmallString)
    jump_password = db.Column(db.SmallString)
    exit_command = db.Column(db.SmallString)
    expect_username_prompt = db.Column(db.SmallString)
    expect_password_prompt = db.Column(db.SmallString)
    expect_prompt = db.Column(db.SmallString)
    expect_string = db.Column(db.SmallString)

    __mapper_args__ = {"polymorphic_identity": "netmiko_prompts_service"}

    def job(self, run, payload, device):
        netmiko_connection = run.netmiko_connection(device)
        netmiko_connection.session_log.truncate(0)
        send_strings = (run.command, run.response1, run.response2, run.response3)
        expect_strings = (run.confirmation1, run.confirmation2, run.confirmation3, None)
        commands, confirmation = [], None
        results = {"commands": commands}
        try:
            prompt = run.enter_remote_device(netmiko_connection, device)
            for send_string, expect_string in zip(send_strings, expect_strings):
                if not send_string:
                    break
                command = run.sub(send_string, locals())
                clean_command = command.replace(netmiko_connection.password, "********")
                commands.append(clean_command)
                run.log(
                    "info",
                    f"Sending '{clean_command}' with Netmiko",
                    device,
                    logger="security",
                )
                confirmation = run.sub(expect_string, locals())
                result = netmiko_connection.send_command(
                    command, expect_string=confirmation, delay_factor=run.delay_factor
                )
                results[command] = {"result": result, "match": confirmation}
            run.exit_remote_device(netmiko_connection, prompt, device)
        except Exception:
            result = (
                netmiko_connection.session_log.getvalue()
                .decode()
                .lstrip("\u0000")
                .replace(netmiko_connection.password, "********")
            )
            return {
                **results,
                **{
                    "error": format_exc(),
                    "result": result,
                    "match": confirmation,
                    "success": False,
                },
            }
        return {"commands": commands, "result": result}


class NetmikoPromptsForm(NetmikoForm):
    form_type = HiddenField(default="netmiko_prompts_service")
    command = StringField(substitution=True)
    confirmation1 = StringField(
        substitution=True, render_kw={"help": "netmiko/confirmation"}
    )
    response1 = StringField(
        substitution=True, render_kw={"help": "netmiko/confirmation"}
    )
    confirmation2 = StringField(
        substitution=True, render_kw={"help": "netmiko/confirmation"}
    )
    response2 = StringField(
        substitution=True, render_kw={"help": "netmiko/confirmation"}
    )
    confirmation3 = StringField(
        substitution=True, render_kw={"help": "netmiko/confirmation"}
    )
    response3 = StringField(
        substitution=True, render_kw={"help": "netmiko/confirmation"}
    )
    groups = {
        "Main Parameters": {
            "commands": [
                "command",
                "confirmation1",
                "response1",
                "confirmation2",
                "response2",
                "confirmation3",
                "response3",
            ],
            "default": "expanded",
        },
        **NetmikoForm.groups,
    }

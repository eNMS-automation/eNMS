from sqlalchemy import Boolean, Float, ForeignKey, Integer
from traceback import format_exc

from eNMS.database import db
from eNMS.fields import BooleanField, HiddenField, StringField
from eNMS.forms import NetmikoForm
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
    read_timeout = db.Column(Float, default=10.0)
    conn_timeout = db.Column(Float, default=10.0)
    auth_timeout = db.Column(Float, default=0.0)
    banner_timeout = db.Column(Float, default=15.0)
    global_delay_factor = db.Column(Float, default=0.1)
    cmd_verify = db.Column(Boolean, default=False)
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

    @staticmethod
    def job(self, run, device):
        send_strings = (run.command, run.response1, run.response2, run.response3)
        expect_strings = (run.confirmation1, run.confirmation2, run.confirmation3, None)
        commands, confirmation, result = [], None, "No command sent"
        if run.dry_run:
            send_strings = [
                run.safe_log(command, run.sub(command, locals()))
                for command in send_strings
            ]
            expect_strings = [run.sub(command, locals()) for command in expect_strings]
            return {"send_strings": send_strings, "expect_strings": expect_strings}
        netmiko_connection = run.netmiko_connection(device)
        netmiko_connection.session_log.session_log.truncate(0)
        results = {"commands": commands}
        try:
            prompt = run.enter_remote_device(netmiko_connection, device)
            for send_string, expect_string in zip(send_strings, expect_strings):
                if not send_string:
                    break
                command = run.sub(send_string, locals())
                safe_command = command.replace(netmiko_connection.password, "********")
                log_command = run.safe_log(send_string, safe_command)
                commands.append(log_command)
                run.log(
                    "info",
                    f"Sending '{log_command}' with Netmiko",
                    device,
                    logger="security",
                )
                confirmation = run.sub(expect_string, locals())
                result = netmiko_connection.send_command(
                    command,
                    expect_string=confirmation,
                    read_timeout=run.read_timeout,
                    cmd_verify=run.cmd_verify,
                )
                results[log_command] = {"result": result, "match": confirmation}
            run.exit_remote_device(netmiko_connection, prompt, device)
        except Exception:
            result = (
                netmiko_connection.session_log.session_log.getvalue()
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
    confirmation1 = StringField(substitution=True, help="netmiko/confirmation")
    response1 = StringField(substitution=True, help="netmiko/confirmation")
    confirmation2 = StringField(substitution=True, help="netmiko/confirmation")
    response2 = StringField(substitution=True, help="netmiko/confirmation")
    confirmation3 = StringField(substitution=True, help="netmiko/confirmation")
    response3 = StringField(substitution=True, help="netmiko/confirmation")
    cmd_verify = BooleanField("Command Verify", default=False)
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
        "Advanced Netmiko Parameters": {
            "commands": ["cmd_verify"],
            "default": "hidden",
        },
    }

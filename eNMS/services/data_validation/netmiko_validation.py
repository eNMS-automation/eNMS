from sqlalchemy import Boolean, Float, ForeignKey, Integer
from traceback import format_exc
from wtforms import BooleanField, HiddenField

from eNMS.database.dialect import Column, LargeString, SmallString
from eNMS.forms.fields import PasswordSubstitutionField, SubstitutionField
from eNMS.forms.automation import NetmikoForm
from eNMS.models.automation import ConnectionService


class NetmikoValidationService(ConnectionService):

    __tablename__ = "netmiko_validation_service"
    pretty_name = "Netmiko Validation"
    parent_type = "connection_service"
    id = Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    enable_mode = Column(Boolean, default=True)
    config_mode = Column(Boolean, default=False)
    command = Column(LargeString)
    driver = Column(SmallString)
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Float, default=10.0)
    delay_factor = Column(Float, default=1.0)
    global_delay_factor = Column(Float, default=1.0)
    use_jumpserver = Column(Boolean)
    jump_command = Column(SmallString)
    jump_username = Column(SmallString)
    jump_password = Column(SmallString)
    exit_command = Column(SmallString)
    expect_username_prompt = Column(SmallString)
    expect_password_prompt = Column(SmallString)
    expect_prompt = Column(SmallString)
    expect_string = Column(SmallString)
    auto_find_prompt = Column(Boolean, default=True)
    strip_prompt = Column(Boolean, default=True)
    strip_command = Column(Boolean, default=True)
    use_genie = Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "netmiko_validation_service"}

    def job(self, run, payload, device):
        netmiko_connection = run.netmiko_connection(device)
        if self.use_jumpserver:
            netmiko_connection.find_prompt()
            prompt = netmiko_connection.base_prompt
            commands = list(filter(None, [
                run.sub(run.jump_command, locals()),
                run.sub(run.expect_username_prompt, locals()),
                run.sub(run.jump_username, locals()),
                run.sub(run.expect_password_prompt, locals()),
                run.sub(run.jump_password, locals()),
                run.sub(run.expect_prompt, locals()),
            ]))
            result = self.enter_jump_server(run, netmiko_connection, commands)
            if result:
                return result
        command = run.sub(run.command, locals())
        run.log("info", f"Sending '{command}' with Netmiko", device)
        expect_string = run.sub(run.expect_string, locals())
        netmiko_connection.session_log.truncate(0)
        try:
            result = netmiko_connection.send_command(
                command,
                delay_factor=run.delay_factor,
                expect_string=expect_string or None,
                auto_find_prompt=run.auto_find_prompt,
                strip_prompt=run.strip_prompt,
                strip_command=run.strip_command,
                use_genie=self.use_genie,
            )
        except Exception:
            return {
                "command": command,
                "error": format_exc(),
                "result": netmiko_connection.session_log.getvalue().decode(),
                "success": False,
            }
        if self.use_jumpserver:
            exit_command = run.sub(run.exit_command, locals())
            netmiko_connection.send_command(
                exit_command,
                expect_string=prompt or None,
                auto_find_prompt=True,
                strip_prompt=False,
                strip_command=True,
            )
        return {"command": command, "result": result}

    def enter_jump_server(self, run, netmiko_connection, commands):
        for (send, expect) in zip(commands[::2], commands[1::2]):
            if not send or not expect:
                continue
            try:
                netmiko_connection.send_command(
                    send,
                    expect_string=expect,
                    auto_find_prompt=False,
                    strip_prompt=False,
                    strip_command=True,
                    max_loops=150,
                )
            except Exception:
                return {
                    "command": send,
                    "error": format_exc(),
                    "result": netmiko_connection.session_log.getvalue().decode(),
                    "message": f"Sent '{send}', waiting for '{expect}'",
                    "success": False,
                }


class NetmikoValidationForm(NetmikoForm):
    form_type = HiddenField(default="netmiko_validation_service")
    command = SubstitutionField()
    expect_string = SubstitutionField()
    auto_find_prompt = BooleanField(default=True)
    strip_prompt = BooleanField(default=True)
    strip_command = BooleanField(default=True)
    use_genie = BooleanField(default=False)
    groups = {
        "Main Parameters": {"commands": ["command"], "default": "expanded"},
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
        **NetmikoForm.groups,
    }

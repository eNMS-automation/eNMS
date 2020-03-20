from sqlalchemy import Boolean, Float, ForeignKey, Integer
from traceback import format_exc
from wtforms import BooleanField, HiddenField

from eNMS.database.dialect import Column, LargeString, SmallString
from eNMS.forms.fields import PasswordSubstitutionField, SubstitutionField
from eNMS.forms.automation import NetmikoForm
from eNMS.models.automation import ConnectionService


class NetmikoPromptsService(ConnectionService):

    __tablename__ = "netmiko_prompts_service"
    pretty_name = "Netmiko Prompts"
    parent_type = "connection_service"
    id = Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    enable_mode = Column(Boolean, default=True)
    config_mode = Column(Boolean, default=False)
    command = Column(SmallString)
    confirmation1 = Column(LargeString, default="")
    response1 = Column(SmallString)
    confirmation2 = Column(LargeString, default="")
    response2 = Column(SmallString)
    confirmation3 = Column(LargeString, default="")
    response3 = Column(SmallString)
    driver = Column(SmallString)
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=10.0)
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

    __mapper_args__ = {"polymorphic_identity": "netmiko_prompts_service"}

    def job(self, run, payload, device):
        netmiko_connection = run.netmiko_connection(device)
        netmiko_connection.session_log.truncate(0)

        if self.use_jumpserver:
            jumpserver_prompt, error = self.enter_jumpserver(run, netmiko_connection)
            if error:
                return error

        send_strings = (run.command, run.response1, run.response2, run.response3)
        expect_strings = (run.confirmation1, run.confirmation2, run.confirmation3, None)
        commands = []
        results = {"commands": commands}
        for send_string, expect_string in zip(send_strings, expect_strings):
            if not send_string:
                break
            command = run.sub(send_string, locals())
            commands.append(command)
            run.log("info", f"Sending '{command}' with Netmiko", device)
            confirmation = run.sub(expect_string, locals())
            try:
                result = netmiko_connection.send_command_timing(
                    command, delay_factor=run.delay_factor
                )
            except Exception:
                return {
                    **results,
                    **{
                        "error": format_exc(),
                        "result": netmiko_connection.session_log.getvalue().decode(),
                        "match": confirmation,
                        "success": False,
                    },
                }
            results[command] = {"result": result, "match": confirmation}
            if confirmation and confirmation not in result:
                results.update(
                    {"success": False, "result": result, "match": confirmation}
                )
                return results

        if self.use_jumpserver:
            self.exit_jumpserver(run, netmiko_connection, jumpserver_prompt)

        return {"commands": commands, "result": result}

    def enter_jumpserver(self, run, netmiko_connection):
        jump_command = run.sub(run.jump_command, locals())
        jump_username = run.sub(run.jump_username, locals())
        jump_password = run.sub(run.jump_password, locals())
        expect_username_prompt = run.sub(run.expect_username_prompt, locals())
        expect_password_prompt = run.sub(run.expect_password_prompt, locals())
        expect_prompt = run.sub(run.expect_prompt, locals())

        if (
            expect_username_prompt
            and not jump_username
            or expect_password_prompt
            and not jump_password
        ):
            raise Exception(
                "Jumpserver username/password is required when a username/password prompt is specified"
            )

        # Grab prompt from jumpserver for use after exit from device
        netmiko_connection.find_prompt()
        jumpserver_prompt = netmiko_connection.base_prompt

        send_strings = (
            text
            for text in (jump_command, jump_username, jump_password)
            if text not in (None, "")
        )
        expect_strings = (
            text
            for text in (expect_username_prompt, expect_password_prompt, expect_prompt)
            if text not in (None, "")
        )

        for send_string, expect_string in zip(send_strings, expect_strings):
            if not (send_string and expect_string):
                return jumpserver_prompt, None
            try:
                netmiko_connection.send_command(
                    send_string,
                    expect_string=expect_string,
                    auto_find_prompt=False,
                    strip_prompt=False,
                    strip_command=True,
                    max_loops=150,  # 150 loops * .2 loop_delay = 30 second timeout
                )
            except Exception:
                return (
                    None,
                    {
                        "error": format_exc(),
                        "result": (
                            netmiko_connection.session_log.getvalue().decode()
                            if hasattr(netmiko_connection, "session_log")
                            else "No results available after exception. Driver does not support session_log"
                        ),
                        "message": f"Sent '{send_string}', waiting for '{expect_string}'",
                        "success": False,
                    },
                )

        return jumpserver_prompt, None

    def exit_jumpserver(self, run, netmiko_connection, jumpserver_prompt):
        exit_command = run.sub(run.exit_command, locals())

        # Send exit command, wait for device prompt
        netmiko_connection.send_command(
            exit_command,
            expect_string=jumpserver_prompt or None,
            auto_find_prompt=True,
            strip_prompt=False,
            strip_command=True,
        )


class NetmikoPromptsForm(NetmikoForm):
    form_type = HiddenField(default="netmiko_prompts_service")
    command = SubstitutionField()
    confirmation1 = SubstitutionField()
    response1 = SubstitutionField()
    confirmation2 = SubstitutionField()
    response2 = SubstitutionField()
    confirmation3 = SubstitutionField()
    response3 = SubstitutionField()

    # Need to add javascript to let service editor choose a profile and
    # populate each field from the chosen profile.
    JUMPSERVER_DEFAULT_PROFILES = {
        "Cisco Calvados": {
            "jump_command": "admin",
            "exit_command": "exit",
            "expect_username_prompt": "Admin Username:",
            "expect_password_prompt": "Password:",
            "expect_prompt": "sysadmin-vm:.*#",
        },
    }

    defaults = JUMPSERVER_DEFAULT_PROFILES["Cisco Calvados"]

    use_jumpserver = BooleanField("Use Jump Server", default=False)
    jump_command = SubstitutionField(
        label="Command that jumps to device", default=defaults["jump_command"]
    )
    jump_username = SubstitutionField(label="Device username")
    jump_password = PasswordSubstitutionField(label="Device jump_password")
    exit_command = SubstitutionField(
        label="Command to exit device back to jump server",
        default=defaults["exit_command"],
    )
    expect_username_prompt = SubstitutionField(
        "Expected username prompt", default=defaults["expect_username_prompt"]
    )
    expect_password_prompt = SubstitutionField(
        "Expected password prompt", default=defaults["expect_password_prompt"]
    )
    expect_prompt = SubstitutionField(
        "Expected prompt after login", default=defaults["expect_prompt"]
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
        "Jump Server Parameters": {
            "commands": [
                "use_jumpserver",
                "jump_command",
                "expect_username_prompt",
                "jump_username",
                "expect_password_prompt",
                "jump_password",
                "expect_prompt",
                "exit_command",
            ],
            "default": "hidden",
        },
        **NetmikoForm.groups,
    }

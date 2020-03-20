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
            jumpserver_prompt, error = self.enter_jumpserver(run, netmiko_connection)
            if error:
                return error

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
            self.exit_jumpserver(run, netmiko_connection, jumpserver_prompt)

        return {"command": command, "result": result}

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


class NetmikoValidationForm(NetmikoForm):
    form_type = HiddenField(default="netmiko_validation_service")
    command = SubstitutionField()

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
    jump_password = PasswordSubstitutionField(label="Device password")
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

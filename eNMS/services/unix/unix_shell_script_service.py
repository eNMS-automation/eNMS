from sqlalchemy import Boolean, Float, ForeignKey, Integer
from wtforms import (
    HiddenField,
    StringField,
    BooleanField,
    IntegerField,
    SelectField,
    FloatField,
)
from wtforms.widgets import TextArea

from eNMS import app
from eNMS.database.dialect import Column, LargeString, SmallString
from eNMS.forms.automation import ServiceForm
from eNMS.forms.services import NetmikoForm
from eNMS.forms.fields import SubstitutionField
from eNMS.models.automation import Service


class UnixShellScriptService(Service):

    __tablename__ = "unix_shell_script_service"

    id = Column(Integer, ForeignKey("service.id"), primary_key=True)
    source_code = Column(LargeString, default="")
    privileged_mode = Column(Boolean, default=False)
    driver = Column(SmallString)
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=10.0)
    delay_factor = Column(Float, default=1.0)
    global_delay_factor = Column(Float, default=1.0)
    expect_string = Column(SmallString)
    auto_find_prompt = Column(Boolean, default=True)
    strip_prompt = Column(Boolean, default=True)
    strip_command = Column(Boolean, default=True)

    __mapper_args__ = {"polymorphic_identity": "unix_shell_script_service"}

    def job(self, run, payload, device):
        netmiko_connection = run.netmiko_connection(device)
        source_code = run.sub(run.source_code, locals())
        script_file_name = f"{self.name}.sh"
        run.log(
            "info",
            f"Sending shell script '{script_file_name}'"
            f" to run on {device.name} (Netmiko)",
        )
        expect_string = run.sub(run.expect_string, locals())
        command_list = [
            f"echo '{source_code}' > '{script_file_name}'",
            f"bash ./{script_file_name}",
            f"rm -f '{script_file_name}'",
        ]
        for command in command_list:
            output = netmiko_connection.send_command(
                command,
                delay_factor=run.delay_factor,
                expect_string=run.expect_string or None,
                auto_find_prompt=run.auto_find_prompt,
                strip_prompt=run.strip_prompt,
                strip_command=run.strip_command,
            )
            if "bash" in command:
                result = output
            return_code = netmiko_connection.send_command(
                f"echo $?",
                delay_factor=run.delay_factor,
                expect_string=run.expect_string or None,
                auto_find_prompt=run.auto_find_prompt,
                strip_prompt=run.strip_prompt,
                strip_command=run.strip_command,
            )
            if return_code != "0":
                break
        return {
            "return_code": return_code,
            "result": result,
            "success": return_code == "0",
        }


class UnixShellScriptForm(ServiceForm, NetmikoForm):
    form_type = HiddenField(default="unix_shell_script_service")
    privileged_mode = BooleanField("Privileged mode (run as root using sudo)")
    source_code = StringField(
        widget=TextArea(),
        render_kw={"rows": 15},
        default=(
            "#!/bin/bash\n"
            "# The following example shell script returns"
            " 0 for success; non-zero for failure\n"
            "directory_contents=`ls -al /root`  # Needs privileged mode\n"
            "return_code=$?\n"
            "if [ $return_code -ne 0 ]; then\n"
            "    exit $return_code  # Indicating Failure\n"
            "else\n"
            '    echo -e "$directory_contents"\n'
            "    exit 0  # Indicating Success\n"
            "fi\n"
        ),
    )
    driver = SelectField(choices=app.NETMIKO_DRIVERS, default="linux")
    use_device_driver = BooleanField(default=True)
    fast_cli = BooleanField()
    timeout = IntegerField(default=10)
    delay_factor = FloatField(default=1.0)
    global_delay_factor = FloatField(default=1.0)
    expect_string = SubstitutionField()
    auto_find_prompt = BooleanField(default=True)
    strip_prompt = BooleanField(default=True)
    strip_command = BooleanField(default=True)
    groups = {
        "Main Parameters": {"commands": ["source_code"], "default": "expanded"},
        "Netmiko Parameters": NetmikoForm.group,
        "Advanced Netmiko Parameters": {
            "commands": [
                "expect_string",
                "auto_find_prompt",
                "strip_prompt",
                "strip_command",
            ],
            "default": "hidden",
        },
    }

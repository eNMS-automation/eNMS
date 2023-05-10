from sqlalchemy import Boolean, Float, ForeignKey, Integer
from wtforms.widgets import TextArea

from eNMS.database import db
from eNMS.forms import NetmikoForm
from eNMS.fields import BooleanField, HiddenField, StringField
from eNMS.models.automation import ConnectionService
from eNMS.variables import vs


class UnixShellScriptService(ConnectionService):
    __tablename__ = "unix_shell_script_service"
    pretty_name = "Unix Shell"
    parent_type = "connection_service"
    id = db.Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    source_code = db.Column(db.LargeString)
    enable_mode = db.Column(Boolean, default=False)
    config_mode = db.Column(Boolean, default=False)
    driver = db.Column(db.SmallString)
    expect_string = db.Column(db.SmallString)
    auto_find_prompt = db.Column(Boolean, default=True)
    strip_prompt = db.Column(Boolean, default=True)
    strip_command = db.Column(Boolean, default=True)

    __mapper_args__ = {"polymorphic_identity": "unix_shell_script_service"}

    def job(self, run, device):
        netmiko_connection = run.netmiko_connection(device)
        source_code = run.sub(run.source_code, locals())
        script_file_name = f"{run.space_deleter(vs.get_time())}.sh"
        run.log("info", f"Sending shell script '{script_file_name}'", device)
        expect_string = run.sub(run.expect_string, locals())
        command_list = (
            f"echo '{source_code}' > '{script_file_name}'",
            f"bash ./{script_file_name}",
            f"rm -f '{script_file_name}'",
        )
        for command in command_list:
            output = netmiko_connection.send_command(
                command,
                expect_string=expect_string or None,
                auto_find_prompt=run.auto_find_prompt,
                strip_prompt=run.strip_prompt,
                strip_command=run.strip_command,
            )
            if "bash" in command:
                result = output
            return_code = netmiko_connection.send_command(
                "echo $?",
                expect_string=expect_string or None,
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


class UnixShellScriptForm(NetmikoForm):
    form_type = HiddenField(default="unix_shell_script_service")
    enable_mode = BooleanField("Run as root using sudo")
    config_mode = BooleanField("Config mode")
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
    auto_find_prompt = BooleanField(default=True)
    expect_string = StringField(substitution=True)
    strip_prompt = BooleanField(default=True)
    strip_command = BooleanField(default=True)
    groups = {
        "Main Parameters": {"commands": ["source_code"], "default": "expanded"},
        "Advanced Netmiko Parameters": {
            "commands": [
                "auto_find_prompt",
                "expect_string",
                "strip_prompt",
                "strip_command",
            ],
            "default": "hidden",
        },
        **NetmikoForm.groups,
    }

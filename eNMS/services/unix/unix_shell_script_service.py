from fabric import Connection
from io import StringIO
from sqlalchemy import Boolean, ForeignKey, Integer
from wtforms import HiddenField, StringField, BooleanField
from wtforms.widgets import TextArea

from eNMS.database.dialect import Column, LargeString
from eNMS.forms.automation import ServiceForm
from eNMS.forms.services import StringValidationForm
from eNMS.models.automation import Run, Service
from eNMS.models.inventory import Device


class UnixShellScriptService(Service):

    __tablename__ = "UnixShellScriptService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    source_code = Column(LargeString, default="")
    content_match = Column(LargeString, default="")
    content_match_regex = Column(Boolean, default=False)
    negative_logic = Column(Boolean, default=False)
    delete_spaces_before_matching = Column(Boolean, default=False)
    privileged_mode = Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "UnixShellScriptService"}

    def job(self, run: "Run", payload: dict, device: Device) -> dict:
        username, password = run.get_credentials(device)
        fabric_connection = Connection(
            host=device.ip_address,
            port=device.port,
            user=username,
            connect_kwargs={"password": password},
        )
        source_code = run.sub(run.source_code, locals())
        match = run.sub(run.content_match, locals())
        run.log("info", f"Running Unix Shell Script {self.name} on {device.name}")
        script_file_name = "unix_shell_script_service.sh"
        with StringIO(run.source_code) as script_file:
            fabric_connection.put(script_file, script_file_name)
            if run.privileged_mode:
                if not device.enable_password:
                    raise Exception(
                        f"Service {self.name} requested privileged mode on device "
                        f"with no configured enable_password: {device.name}"
                    )
                result = fabric_connection.sudo(
                    f"bash {script_file_name}", password=device.enable_password
                )
            else:
                result = fabric_connection.run(f"bash {script_file_name}")
            fabric_connection.run(f"rm {script_file_name}")

        return {
            "match": match,
            "negative_logic": run.negative_logic,
            "result": f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
            "success": result.ok and run.match_content(result, match),
        }


class UnixShellScriptForm(ServiceForm, StringValidationForm):
    form_type = HiddenField(default="UnixShellScriptService")
    privileged_mode = BooleanField("Privileged mode (run as root using sudo)")
    source_code = StringField(
        widget=TextArea(),
        render_kw={"rows": 15},
        default=(
            "# The following example shell script returns "
            "0 for success; non-zero for failure\n"
            "#!/bin/bash\n"
            "directory_contents=`ls -al /root`  # Needs privileged mode\n"
            "echo $directory_contents\n"
            "exit 0 # Success\n"
        ),
    )

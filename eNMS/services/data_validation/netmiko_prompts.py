import traceback

from sqlalchemy import Boolean, Float, ForeignKey, Integer
from wtforms import HiddenField

from eNMS.database.dialect import Column, LargeString, SmallString
from eNMS.forms.fields import SubstitutionField
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

    __mapper_args__ = {"polymorphic_identity": "netmiko_prompts_service"}

    def job(self, run, payload, device):
        netmiko_connection = run.netmiko_connection(device)

        send_strings = (run.command, run.response1, run.response2, run.response3)
        expect_strings = (run.confirmation1, run.confirmation2, run.confirmation3, None)

        commands = []
        results = {"commands": commands}
        for send_string, expect_string in zip(send_strings, expect_strings):
            command = run.sub(send_string, locals())
            if len(command) == 0:
                break # Stop when no commmand or response
            commands.append(command)
            run.log("info", f"Sending '{command}' with Netmiko", device)
            
            try:
                result = netmiko_connection.send_command_timing(
                    command, delay_factor=run.delay_factor
                )
            except Exception as exc:
                results.update({
                    "error": traceback.format_exc(),
                    "result": netmiko_connection.session_log.getvalue().decode(),
                    "match": confirmation,
                    "success": False,
                    })
                return results

            confirmation = run.sub(expect_string, locals())
            results[command] = {"result": result, "match": confirmation}
            if confirmation and confirmation not in result:
                results.update({"success": False, "result": result, "match": confirmation})
                return results

        return {"commands": commands, "result": result}


class NetmikoPromptsForm(NetmikoForm):
    form_type = HiddenField(default="netmiko_prompts_service")
    command = SubstitutionField()
    confirmation1 = SubstitutionField()
    response1 = SubstitutionField()
    confirmation2 = SubstitutionField()
    response2 = SubstitutionField()
    confirmation3 = SubstitutionField()
    response3 = SubstitutionField()
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

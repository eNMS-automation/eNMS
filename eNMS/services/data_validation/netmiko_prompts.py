from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer
from wtforms import HiddenField

from eNMS.database.dialect import LargeString, MutableDict, SmallString
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.forms.services import NetmikoForm, ValidationForm
from eNMS.models.automation import Run, Service
from eNMS.models.inventory import Device


class NetmikoPromptsService(Service):

    __tablename__ = "NetmikoPromptsService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    privileged_mode = Column(Boolean, default=False)
    command = Column(SmallString, default="")
    confirmation1 = Column(LargeString, default="")
    response1 = Column(SmallString, default="")
    confirmation2 = Column(LargeString, default="")
    response2 = Column(SmallString, default="")
    confirmation3 = Column(LargeString, default="")
    response3 = Column(SmallString, default="")
    conversion_method = Column(SmallString, default="text")
    validation_method = Column(SmallString, default="text")
    content_match = Column(LargeString, default="")
    content_match_regex = Column(Boolean, default=False)
    dict_match = Column(MutableDict, default={})
    negative_logic = Column(Boolean, default=False)
    delete_spaces_before_matching = Column(Boolean, default=False)
    driver = Column(SmallString, default="")
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=10.0)
    delay_factor = Column(Float, default=1.0)
    global_delay_factor = Column(Float, default=1.0)

    __mapper_args__ = {"polymorphic_identity": "NetmikoPromptsService"}

    def job(self, run: "Run", payload: dict, device: Device) -> dict:
        netmiko_connection = run.netmiko_connection(device)
        command = run.sub(run.command, locals())
        run.log("info", f"Sending '{command}' on {device.name} (Netmiko)")
        commands = [command]
        results = {"commands": commands}
        result = netmiko_connection.send_command_timing(
            command, delay_factor=run.delay_factor
        )
        response1 = run.sub(run.response1, locals())
        confirmation1 = run.sub(run.confirmation1, locals())
        results[command] = {"result": result, "match": confirmation1}
        if confirmation1 not in result:
            results.update({"success": False, "result": result, "match": confirmation1})
            return results
        elif response1:
            result = netmiko_connection.send_command_timing(
                response1, delay_factor=run.delay_factor
            )
            confirmation2 = run.sub(run.confirmation2, locals())
            commands.append(confirmation2)
            results[response1] = {"result": result, "match": confirmation2}
            response2 = run.sub(run.response2, locals())
            if confirmation2 not in result:
                results.update(
                    {"success": False, "result": result, "match": confirmation2}
                )
                return results
            elif response2:
                result = netmiko_connection.send_command_timing(
                    response2, delay_factor=run.delay_factor
                )
                confirmation3 = run.sub(run.confirmation3, locals())
                commands.append(confirmation3)
                results[response2] = {"result": result, "match": confirmation3}
                response3 = run.sub(run.response3, locals())
                if confirmation3 not in result:
                    results.update(
                        {"success": False, "result": result, "match": confirmation3}
                    )
                    return results
                elif response3:
                    result = netmiko_connection.send_command_timing(
                        response3, delay_factor=run.delay_factor
                    )
        match = run.sub(run.content_match, locals())
        return {
            "commands": commands,
            "expected": match if run.validation_method == "text" else run.dict_match,
            "negative_logic": run.negative_logic,
            "result": result,
            "success": run.match_content(result, match),
        }


class NetmikoPromptsForm(ServiceForm, NetmikoForm, ValidationForm):
    form_type = HiddenField(default="NetmikoPromptsService")
    command = SubstitutionField()
    confirmation1 = SubstitutionField()
    response1 = SubstitutionField()
    confirmation2 = SubstitutionField()
    response2 = SubstitutionField()
    confirmation3 = SubstitutionField()
    response3 = SubstitutionField()
    groups = {
        "Main Parameters": [
            "command",
            "confirmation1",
            "response1",
            "confirmation2",
            "response2",
            "confirmation3",
            "response3",
        ],
        "Netmiko Parameters": NetmikoForm.group,
        "String Validation Parameters": ValidationForm.group,
    }

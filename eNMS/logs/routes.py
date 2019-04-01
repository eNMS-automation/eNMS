from flask import request

from eNMS.functions import get, serialize
from eNMS.properties import log_public_properties, log_rule_table_properties
from eNMS.logs import bp
from eNMS.logs.forms import LogAutomationForm


@get(bp, "/log_management", "View")
def log_management() -> dict:
    return dict(fields=log_public_properties, logs=serialize("Log"))


@get(bp, "/log_automation", "View")
def log_automation() -> dict:
    return dict(
        log_automation_form=LogAutomationForm(request.form),
        fields=log_rule_table_properties,
        log_rules=serialize("LogRule"),
    )

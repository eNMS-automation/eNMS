from flask import jsonify, request
from re import search

from eNMS.base.helpers import get, post, serialize
from eNMS.logs import bp
from eNMS.logs.forms import LogAutomationForm, LogFilteringForm


@get(bp, '/log_management', 'View')
def log_management():
    return dict(
        log_filtering_form=LogFilteringForm(request.form),
        fields=('source', 'content'),
        logs=serialize('Log')
    )


@get(bp, '/log_automation', 'View')
def log_automation():
    return dict(
        log_automation_form=LogAutomationForm(request.form, 'Task'),
        fields=('name', 'source', 'content'),
        log_rules=serialize('LogRule')
    )


@post(bp, '/filter_logs', 'Edit')
def filter_logs():
    logs = [log for log in serialize('Log') if all(
        request.form[prop] in str(val) if not prop + 'regex' in request.form
        else search(request.form[prop], str(val)) for prop, val in log.items()
        if prop in request.form and request.form[prop]
    )]
    return jsonify(logs)

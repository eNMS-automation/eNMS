from flask import jsonify, render_template, request
from re import search

from eNMS import db
from eNMS.base.helpers import (
    choices,
    delete,
    factory,
    fetch,
    get,
    objectify,
    post,
    serialize
)
from eNMS.base.properties import pretty_names
from eNMS.logs import bp
from eNMS.logs.forms import LogAutomationForm, LogFilteringForm


@get(bp, '/log_management', 'View')
def log_management():
    return render_template(
        'log_management.html',
        log_filtering_form=LogFilteringForm(request.form),
        names=pretty_names,
        fields=('source', 'content'),
        logs=serialize('Log')
    )


@get(bp, '/log_automation', 'View')
def syslog_automation():
    return render_template(
        'log_automation.html',
        log_automation_form=LogAutomationForm(request.form, 'Task'),
        names=pretty_names,
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

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


@get(bp, '/log_management', 'Logs Section')
def log_management():
    return render_template(
        'log_management.html',
        log_filtering_form=LogFilteringForm(request.form),
        names=pretty_names,
        fields=('source', 'content'),
        logs=serialize('Log')
    )


@get(bp, '/log_automation', 'Logs Section')
def syslog_automation():
    return render_template(
        'log_automation.html',
        log_automation_form=LogAutomationForm(request.form, 'Task'),
        names=pretty_names,
        fields=('name', 'source', 'content'),
        log_rules=serialize('LogRule')
    )


@post(bp, '/delete_log/<log_id>', 'Edit Logs Section')
def delete_log(log_id):
    return jsonify(delete('Log', id=log_id))


@post(bp, '/filter_logs', 'Edit Logs Section')
def filter_logs():
    logs = [log for log in serialize('Log') if all(
        request.form[prop] in str(val) if not prop + 'regex' in request.form
        else search(request.form[prop], str(val)) for prop, val in log.items()
        if prop in request.form and request.form[prop]
    )]
    return jsonify(logs)


@post(bp, '/get_log_rule/<log_rule_id>', 'Logs Section')
def get_log_rule(log_rule_id):
    return jsonify(fetch('LogRule', id=log_rule_id).serialized)


@post(bp, '/save_log_rule', 'Edit Logs Section')
def save_log_rule():
    return jsonify(factory('LogRule', **request.form).serialized)


@post(bp, '/delete_log_rule/<log_id>', 'Edit Logs Section')
def delete_log_rule(log_id):
    return jsonify(delete('LogRule', id=log_id))

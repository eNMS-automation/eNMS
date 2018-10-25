from flask import jsonify, render_template, request
from flask_login import login_required
from re import search

from eNMS import db
from eNMS.automation.models import Job
from eNMS.base.custom_base import factory
from eNMS.base.helpers import permission_required, get
from eNMS.base.properties import pretty_names
from eNMS.logs import blueprint
from eNMS.logs.forms import LogAutomationForm, LogFilteringForm
from eNMS.logs.models import Log, LogRule


@blueprint.route('/log_management')
@login_required
@permission_required('Logs Section')
def log_management():
    log_filtering_form = LogFilteringForm(request.form)
    return render_template(
        'log_management.html',
        log_filtering_form=log_filtering_form,
        names=pretty_names,
        fields=('source', 'content'),
        logs=Log.serialize()
    )


@blueprint.route('/log_automation')
@login_required
@permission_required('Logs Section')
def syslog_automation():
    log_automation_form = LogAutomationForm(request.form)
    log_automation_form.jobs.choices = Job.choices()
    return render_template(
        'log_automation.html',
        log_automation_form=log_automation_form,
        names=pretty_names,
        fields=('name', 'source', 'content'),
        log_rules=LogRule.serialize()
    )


@blueprint.route('/delete_log/<log_id>', methods=['POST'])
@login_required
@permission_required('Edit Logs Section', redirect=False)
def delete_log(log_id):
    log = get(Log, id=log_id)
    db.session.delete(log)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/filter_logs', methods=['POST'])
@login_required
@permission_required('Logs Section')
def filter_logs():
    logs = [log for log in Log.serialize() if all(
        # if the regex property is not in the request, the
        # regex box is unticked and we only check that the values of the
        # filters are contained in the values of the log
        request.form[prop] in str(val) if not prop + 'regex' in request.form
        # if it is ticked, we use re.search to check that the value
        # of the device property matches the regular expression,
        # providing that the property field in the form is not empty
        # (empty field <==> property ignored)
        else search(request.form[prop], str(val)) for prop, val in log.items()
        if prop in request.form and request.form[prop]
    )]
    return jsonify(logs)


@blueprint.route('/get_log_rule/<log_rule_id>', methods=['POST'])
@login_required
@permission_required('Logs Section')
def get_log_rule(log_rule_id):
    return jsonify(get(LogRule, id=log_rule_id).serialized)


@blueprint.route('/save_log_rule', methods=['POST'])
@login_required
@permission_required('Edit Logs Section', redirect=False)
def save_log_rule():
    data = request.form.to_dict()
    data['jobs'] = [
        get(Job, id=id) for id in request.form.getlist('jobs')
    ]
    log_rule = factory(LogRule, **data)
    db.session.commit()
    return jsonify(log_rule.serialized)


@blueprint.route('/delete_log_rule/<log_id>', methods=['POST'])
@login_required
@permission_required('Edit Logs Section', redirect=False)
def delete_log_rule(log_id):
    log_rule = get(LogRule, id=log_id)
    db.session.delete(log_rule)
    db.session.commit()
    return jsonify({'success': True})

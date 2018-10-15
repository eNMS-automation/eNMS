from flask import jsonify, render_template, request
from flask_login import login_required

from eNMS.logs.forms import LogAutomationForm
from eNMS.base.custom_base import factory
from eNMS.base.helpers import permission_required, retrieve


@blueprint.route('/syslog_automation')
@login_required
def syslog_automation():
    log_automation_form = LogAutomationForm(request.form)
    log_automation_form.tasks.choices = Task.choices()
    return render_template(
        'log_automation.html',
        log_automation_form=log_automation_form,
        names=pretty_names,
        fields=('name', 'source', 'content'),
        log_rules=LogRule.serialize()
    )


@blueprint.route('/get_log_rule/<log_rule_id>', methods=['POST'])
@login_required
@permission_required('Automation section', redirect=False)
def get_log_rule(log_rule_id):
    return jsonify(retrieve(LogRule, id=log_rule_id).serialized)


@blueprint.route('/save_log_rule', methods=['POST'])
@login_required
@permission_required('Edit log rules', redirect=False)
def save_log_rule():
    data = request.form.to_dict()
    data['tasks'] = [
        retrieve(Task, id=id) for id in request.form.getlist('tasks')
    ]
    log_rule = factory(LogRule, **data)
    db.session.commit()
    return jsonify(log_rule.serialized)


@blueprint.route('/delete_log_rule/<log_id>', methods=['POST'])
@login_required
@permission_required('Edit log rules', redirect=False)
def delete_log_rule(log_id):
    log_rule = retrieve(LogRule, id=log_id)
    db.session.delete(log_rule)
    db.session.commit()
    return jsonify({'success': True})
from base.properties import pretty_names
from flask import Blueprint, render_template, request
from flask_login import login_required
from .forms import LogFilteringForm, SyslogServerForm
from .models import Log, SyslogServer
from re import search

blueprint = Blueprint(
    'logs_blueprint',
    __name__,
    url_prefix='/logs',
    template_folder='templates',
    static_folder='static'
)

from base.database import db


@blueprint.route('/overview', methods=['GET', 'POST'])
@login_required
def logs():
    form = LogFilteringForm(request.form)
    if request.method == 'POST':
        for log in Log.query.all():
            log.visible = all(
                # if the node-regex property is not in the request, the
                # regex box is unticked and we only check that the values
                # are equal.
                str(value) == request.form[property]
                if not property + 'regex' in request.form
                # if it is ticked, we use re.search to check that the value
                # of the node property matches the regular expression.
                else search(request.form[property], str(value))
                for property, value in log.__dict__.items()
                # we consider only the properties in the form
                # providing that the property field in the form is not empty
                # (empty field <==> property ignored)
                if property in request.form and request.form[property]
            )
    # the visible status was updated, we need to commit the change
    db.session.commit()
    return render_template(
        'logs_overview.html',
        form=form,
        names=pretty_names,
        logs=Log.visible_objects(),
    )


@blueprint.route('/syslog_server', methods=['GET', 'POST'])
@login_required
def syslog_server():
    if request.method == 'POST':
        syslog_server = SyslogServer(**request.form)
        db.session.add(syslog_server)
        db.session.commit()
    return render_template(
        'syslog_server.html',
        form=SyslogServerForm(request.form)
    )

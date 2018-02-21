from base.properties import pretty_names
from flask import Blueprint, render_template, request
from flask_login import login_required
from .models import Log
from .forms import SyslogServerForm

blueprint = Blueprint(
    'logs_blueprint', 
    __name__, 
    url_prefix = '/logs', 
    template_folder = 'templates',
    static_folder = 'static'
    )

from base.database import db
from .models import SyslogServer

@blueprint.route('/overview')
@login_required
def logs():
    return render_template(
        'logs_overview.html',
        fields = ('source', 'content'),
        names = pretty_names,  
        logs = Log.query.all()
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
        form = SyslogServerForm(request.form)
        )